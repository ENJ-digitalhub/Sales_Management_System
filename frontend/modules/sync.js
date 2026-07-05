// frontend/modules/sync.js
import { getToken, getDeviceId, BASE_URL } from "./auth.js";
import { getPending, updateStatus, getAllQueued, getPendingCount } from "./queue.js";

const MAX_BATCH_SIZE = 20;
const MAX_RETRIES = 5;
const BACKOFF_SCHEDULE = [1000, 2000, 4000, 8000]; // ms — 4 delays between 5 attempts

let syncInProgress = false;
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
 */
export async function retryFailed() {
  const all = await getAllQueued();
  const failedItems = all.filter(
    (r) => r.status === "FAILED" && r.retry_count < MAX_RETRIES
  );

  for (const item of failedItems) {
    await retryWithBackoff(item, 0);
  }
}

function retryWithBackoff(item, attemptIndex) {
  return new Promise((resolve) => {
    const delay = BACKOFF_SCHEDULE[attemptIndex] ?? BACKOFF_SCHEDULE[BACKOFF_SCHEDULE.length - 1];

    setTimeout(async () => {
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
        const nextAttempt = attemptIndex + 1;
        const attemptsUsed = item.retry_count + nextAttempt;

        if (stillFailing && nextAttempt < BACKOFF_SCHEDULE.length && attemptsUsed < MAX_RETRIES) {
          await retryWithBackoff(item, nextAttempt);
        }
        // else: either succeeded, hit a terminal state (conflict), or
        // exhausted MAX_RETRIES — stop retrying either way.
      } catch (err) {
        // Network still down (or auth failed) — leave it FAILED, next
        // manual/auto sync cycle will pick it up again from scratch.
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
    await pullAndRefresh();

    const transactions = await getQueuedTransactions();
    const batches = [];
    for (let i = 0; i < transactions.length; i += MAX_BATCH_SIZE) {
      batches.push(transactions.slice(i, i + MAX_BATCH_SIZE));
    }

    let totalSynced = 0;
    let totalConflict = 0;
    let totalFailed = 0;

    for (const batch of batches) {
      const results = await pushBatch(batch);
      await processSyncResults(results);

      for (const r of results) {
        if (r.status === "synced") totalSynced++;
        else if (r.status === "conflict") totalConflict++;
        else totalFailed++;
      }
    }

    notify("online");
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
window.addEventListener("online", () => {
  notify("online");
  syncNow();
});

window.addEventListener("offline", () => {
  notify("offline");
});