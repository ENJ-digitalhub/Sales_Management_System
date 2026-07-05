// frontend/modules/sync_ui.js
import { syncNow, setStatusListener, retryFailed } from "./sync.js";
import { getPendingCount, getAllQueued } from "./queue.js";

async function updateBadge() {
  const count = await getPendingCount();
  const badge = document.getElementById("sync-pending-badge");
  if (badge) {
    badge.textContent = count > 0 ? `${count} pending` : "";
    badge.style.display = count > 0 ? "inline" : "none";
  }
}

function updateBanner(state) {
  const banner = document.getElementById("connection-banner");
  if (!banner) return;

  if (state === "auth_error") {
    banner.textContent = "Session expired — please log in again";
    banner.className = "banner-offline";
    banner.style.display = "block";
  } else if (state === "offline" || !navigator.onLine) {
    banner.textContent = "Offline Mode";
    banner.className = "banner-offline";
    banner.style.display = "block";
  } else if (state === "syncing") {
    banner.textContent = "Syncing...";
    banner.className = "banner-syncing";
    banner.style.display = "block";
  } else {
    banner.style.display = "none";
  }
}

export async function renderSyncHistory() {
  const container = document.getElementById("sync-history-list");
  if (!container) return;

  const all = await getAllQueued();
  container.innerHTML = "";

  const statusLabel = {
    SYNCED: { text: "Synced ✓", className: "status-synced" },
    PENDING: { text: "Not Synced", className: "status-pending" },
    FAILED: { text: "Failed", className: "status-failed" },
    CONFLICT: { text: "Conflict", className: "status-conflict" },
  };

  for (const record of all) {
    const label = statusLabel[record.status] || { text: record.status, className: "" };
    const row = document.createElement("div");
    row.className = "sync-history-row";
    row.innerHTML = `
      <span>${record.transaction_id.slice(0, 8)}...</span>
      <span class="${label.className}">${label.text}</span>
      <span>retries: ${record.retry_count}</span>
    `;
    container.appendChild(row);
  }
}

export function initSyncUI() {
  setStatusListener((state) => {
    updateBanner(state);
    updateBadge();
    renderSyncHistory();
  });

  window.addEventListener("online", () => updateBanner("online"));
  window.addEventListener("offline", () => updateBanner("offline"));

  const syncBtn = document.getElementById("sync-now-btn");
  if (syncBtn) {
    syncBtn.addEventListener("click", async () => {
      const result = await syncNow();
      if (result.error) {
        alert(`Sync failed: ${result.error}`);
      } else if (!result.skipped) {
        alert(`Synced: ${result.synced}, Conflicts: ${result.conflict}, Failed: ${result.failed}`);
      }
      await updateBadge();
      await renderSyncHistory();
    });
  }

  const retryBtn = document.getElementById("retry-failed-btn");
  if (retryBtn) {
    retryBtn.addEventListener("click", async () => {
      await retryFailed();
      await updateBadge();
      await renderSyncHistory();
    });
  }

  updateBanner(navigator.onLine ? "online" : "offline");
  updateBadge();
  renderSyncHistory();
}
// add near the bottom of sync_ui.js, alongside the other exports
export async function refreshSyncUI() {
  await updateBadge();
  await renderSyncHistory();
}