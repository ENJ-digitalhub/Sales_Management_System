// frontend/modules/sync.js
import { getToken, getDeviceId, BASE_URL } from "./auth.js";
import { getPending, updateStatus, getAllQueued, getPendingCount } from "./queue.js";

const MAX_BATCH_SIZE = 20;
const MAX_RETRIES = 5;
const BACKOFF_SCHEDULE = [1000, 2000, 4000, 8000]; // ms — 4 delays between 5 attempts

let syncInProgress = false;
let retryInProgress = false;
let onStatusChange = null; // UI callback, set via setStatusListener()

export function setStatusListener(callback) {
  onStatusChange = callback;
}

function notify(state) {
  if (onStatusChange) onStatusChange(state);
}

/** Reads pending items from IndexedDB, formatted for the sync engine. */
export async function getQueuedTransactions() {
  const pending = await getPending();
  return pending.map((record) => ({
    transaction_id: record.transaction_id,
    entity_type: record.entity_type,
    operation: record.operation,
    payload: record.payload,
    created_at: record.created_at,
  }));
}

/** Returns count of pending (not-yet-synced) items — for the UI badge. */
export async function getPendingBadgeCount() {
  const all = await getAllQueued();
  return all.filter((r) => r.status === "PENDING" || r.status === "FAILED").length;
}

/** Sends a batch (max 20) to POST /sync, returns per-item results. */
export async function pushBatch(transactions) {
  if (transactions.length === 0) return [];
  const batch = transactions.slice(0, MAX_BATCH_SIZE);

  const response = await fetch(`${BASE_URL}/sync`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
    },
    body: JSON.stringify({
      device_id: getDeviceId(),
      transactions: batch,
    }),
  });

  if (response.status === 401) {
    throw new Error("AUTH_ERROR");
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Sync push failed");
  }
  return data.results;
}

/** Updates IndexedDB status for each item based on server results. */
export async function processSyncResults(results) {
  for (const result of results) {
    const status = result.status.toUpperCase(); // SYNCED | FAILED | CONFLICT
    const shouldBumpRetry = status === "FAILED";
    await updateStatus(result.transaction_id, status, shouldBumpRetry);
  }
}

/** Pulls fresh product/user data from the server — called before pushing on reconnect. */
export async function pullAndRefresh() {
  const response = await fetch(`${BASE_URL}/sync/pull`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });

  if (response.status === 401) {
    throw new Error("AUTH_ERROR");
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Pull failed");
  }
  return data.data; // { products, users, deleted_product_ids }
}

/**
 * Retries only FAILED items with exponential backoff (1s, 2s, 4s, 8s),
 * implemented via a recursive setTimeout chain rather than nested
 * setTimeout calls — each attempt schedules the next one only after
 * the previous attempt's response comes back, up to MAX_RETRIES total
 * attempts per item.
 *
 * Guarded by retryInProgress so overlapping calls (e.g. the 'online'
 * handler firing right after the 30s safety-net interval) can't start
 * a second backoff chain for the same item while one is already running,
 * which would double-increment retry_count without real elapsed delays
 * between attempts.
 */
export async function retryFailed() {
  if (retryInProgress) return;
  retryInProgress = true;

  try {
    const all = await getAllQueued();
    const failedItems = all.filter(
      (r) => r.status === "FAILED" && r.retry_count < MAX_RETRIES
    );

    for (const item of failedItems) {
      await retryWithBackoff(item, 0);
    }
  } finally {
    retryInProgress = false;
  }
}

function retryWithBackoff(item, attemptIndex) {
  return new Promise((resolve) => {
    const delay = BACKOFF_SCHEDULE[attemptIndex] ?? BACKOFF_SCHEDULE[BACKOFF_SCHEDULE.length - 1];

    setTimeout(async () => {
      const nextAttempt = attemptIndex + 1;
      const attemptsUsed = item.retry_count + nextAttempt;
      const canContinue = nextAttempt < BACKOFF_SCHEDULE.length && attemptsUsed < MAX_RETRIES;

      try {
        const results = await pushBatch([
          {
            transaction_id: item.transaction_id,
            entity_type: item.entity_type,
            operation: item.operation,
            payload: item.payload,
            created_at: item.created_at,
          },
        ]);
        await processSyncResults(results);

        const outcome = results[0];
        const stillFailing = outcome.status === "failed";

        if (stillFailing && canContinue) {
          await retryWithBackoff(item, nextAttempt);
        }
        // else: succeeded, hit a terminal state (conflict), or
        // exhausted MAX_RETRIES — stop retrying either way.
      } catch (err) {
        // Network/server unreachable on this attempt. A network-level
        // failure and a server-returned "failed" status both need to
        // continue the SAME backoff chain — previously this branch
        // marked FAILED and stopped immediately, meaning one dead
        // connection ended retries after only ONE attempt instead of
        // running the full 1s/2s/4s/8s schedule.
        try {
          await updateStatus(item.transaction_id, "FAILED", true);
        } catch (_) {
          // best-effort — if this also fails, next sync cycle will retry anyway
        }

        if (canContinue) {
          await retryWithBackoff(item, nextAttempt);
        }
      }
      resolve();
    }, delay);
  });
}

/**
 * Full sync cycle: pull fresh server state first, then push the queue.
 * Guarded by syncInProgress so overlapping triggers (auto + manual)
 * can't race each other.
 */
export async function syncNow() {
  if (syncInProgress) {
    return { skipped: true };
  }
  syncInProgress = true;
  notify("syncing");

  try {
    // Pull first, per the locked rule — but if the pull itself fails
    // because the server is unreachable (not an auth error), don't
    // abort the whole cycle. Continuing on to the push attempt below
    // means a genuinely dead server still results in queued items
    // being marked FAILED (and becoming retry-eligible), instead of
    // the entire sync cycle bailing out before ever touching the queue.
    try {
      await pullAndRefresh();
    } catch (err) {
      if (err.message === "AUTH_ERROR") throw err;
      // Server unreachable during pull — proceed to push attempt anyway.
    }

    const transactions = await getQueuedTransactions();
    const batches = [];
    for (let i = 0; i < transactions.length; i += MAX_BATCH_SIZE) {
      batches.push(transactions.slice(i, i + MAX_BATCH_SIZE));
    }

    let totalSynced = 0;
    let totalConflict = 0;
    let totalFailed = 0;

    for (const batch of batches) {
      let results;
      try {
        results = await pushBatch(batch);
      } catch (err) {
        if (err.message === "AUTH_ERROR") throw err;

        // Network/server unreachable (fetch itself threw) — this never
        // reaches processSyncResults() below, so without this branch
        // every item in the batch would stay stuck at its previous
        // status forever, with no retry and no visible failure state.
        for (const txn of batch) {
          await updateStatus(txn.transaction_id, "FAILED", true);
          totalFailed++;
        }
        continue;
      }

      await processSyncResults(results);

      for (const r of results) {
        if (r.status === "synced") totalSynced++;
        else if (r.status === "conflict") totalConflict++;
        else totalFailed++;
      }
    }

    notify(totalFailed > 0 ? "offline" : "online");
    return { synced: totalSynced, conflict: totalConflict, failed: totalFailed };
  } catch (err) {
    if (err.message === "AUTH_ERROR") {
      notify("auth_error");
    } else {
      notify("offline");
    }
    return { error: err.message };
  } finally {
    syncInProgress = false;
  }
}

// Reconnect detection — pull first, then push, per the locked rule.
// After a normal sync cycle completes, also run retryFailed() so any
// FAILED items get picked up immediately rather than waiting for the
// next 'online' event or the periodic check below.
window.addEventListener("online", () => {
  notify("online");
  syncNow().then(() => retryFailed());
});

window.addEventListener("offline", () => {
  notify("offline");
});

// Safety net: while the browser reports itself online, periodically
// check for FAILED items and retry them. This covers the case where
// the *server* (not the network) was down and came back — the browser
// never fired a fresh 'online' event for that, since as far as the
// browser is concerned it was online the whole time.
setInterval(() => {
  if (navigator.onLine && !syncInProgress && !retryInProgress) {
    retryFailed();
  }
}, 30000);