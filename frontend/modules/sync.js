// frontend/modules/sync.js
import { getToken, BASE_URL } from "./auth.js";
import { getPending, updateStatus, getPendingCount } from "./queue.js";

let syncInProgress = false;

export async function processQueue() {
  if (syncInProgress) {
    return { skipped: true, reason: "sync already in progress", synced: 0, failed: 0 };
  }
  syncInProgress = true;

  const results = { synced: 0, failed: 0 };

  try {
    const pending = await getPending();

    for (const record of pending) {
      try {
        const response = await fetch(`${BASE_URL}/sales`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${getToken()}`,
          },
          body: JSON.stringify(record.payload),
        });

        if (response.ok) {
          await updateStatus(record.transaction_id, "SYNCED");
          results.synced += 1;
        } else {
          await updateStatus(record.transaction_id, "FAILED", true);
          results.failed += 1;
        }
      } catch (networkError) {
        await updateStatus(record.transaction_id, "PENDING", true);
        results.failed += 1;
      }
    }
  } finally {
    syncInProgress = false;
  }

  return results;
}

export async function getPendingBadgeCount() {
  return getPendingCount();
}

window.addEventListener("online", () => {
  processQueue();
});