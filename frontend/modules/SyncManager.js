
import { pushChanges, pullChanges, resolveConflict } from "../services/api";
import { getAllItems, addItem, putItem, deleteItem, clearStore } from "../services/local_db";

const SYNC_INTERVAL = 5 * 60 * 1000; // 5 minutes
const SYNC_QUEUE_STORE = "sync_queue";
const LAST_SYNC_TIME_KEY = "last_sync_time";

class SyncManager {
  constructor(authService) {
    this.authService = authService;
    this.isSyncing = false;
    this.syncInterval = null;
  }

  startSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
    this.syncInterval = setInterval(() => this.sync(), SYNC_INTERVAL);
    console.log("SyncManager started. Syncing every", SYNC_INTERVAL / 1000, "seconds.");
    this.sync(); // Initial sync on start
  }

  stopSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
    console.log("SyncManager stopped.");
  }

  async enqueueChange(entityType, operation, payload) {
    const transactionId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const change = {
      transaction_id: transactionId,
      entity_type: entityType,
      operation: operation,
      payload: payload,
      status: "pending",
      timestamp: new Date().toISOString(),
    };
    await addItem(SYNC_QUEUE_STORE, change);
    console.log("Change enqueued:", change);
    this.sync(); // Attempt to sync immediately after enqueuing
  }

  async sync() {
    if (this.isSyncing || !this.authService.user) {
      console.log("Skipping sync: already syncing or not authenticated.");
      return;
    }

    this.isSyncing = true;
    console.log("Starting sync process...");

    try {
      // 1. Push local changes to server
      const localChanges = await getAllItems(SYNC_QUEUE_STORE);
      if (localChanges.length > 0) {
        console.log("Pushing local changes:", localChanges);
        const pushResponse = await pushChanges(localChanges);
        if (pushResponse.success) {
          for (const result of pushResponse.results) {
            if (result.status === "enqueued" || result.status === "success") {
              await deleteItem(SYNC_QUEUE_STORE, result.transaction_id);
            } else if (result.status === "conflict") {
              // Handle conflict: mark as conflict in local DB, potentially prompt user
              const conflictedChange = await getItem(SYNC_QUEUE_STORE, result.transaction_id);
              if (conflictedChange) {
                conflictedChange.status = "conflict";
                conflictedChange.server_payload = result.server_payload; // Store server version
                await putItem(SYNC_QUEUE_STORE, conflictedChange);
              }
            }
          }
          console.log("Local changes pushed successfully.");
        } else {
          console.error("Failed to push changes:", pushResponse.message);
        }
      }

      // 2. Pull changes from server
      const lastSyncTime = localStorage.getItem(LAST_SYNC_TIME_KEY) || new Date(0).toISOString();
      console.log("Pulling changes since:", lastSyncTime);
      const pullResponse = await pullChanges(new Date(lastSyncTime));

      if (pullResponse.success) {
        const { products, sales } = pullResponse.changes;

        // Apply pulled changes to local database
        for (const product of products) {
          await putItem("products", product);
        }
        for (const sale of sales) {
          await putItem("sales", sale);
        }
        // Update other entities

        localStorage.setItem(LAST_SYNC_TIME_KEY, new Date().toISOString());
        console.log("Changes pulled and applied successfully.");
      } else {
        console.error("Failed to pull changes:", pullResponse.message);
      }
    } catch (err) {
      console.error("Sync failed:", err);
    } finally {
      this.isSyncing = false;
      console.log("Sync process finished.");
    }
  }

  async resolveConflict(transactionId, resolutionPayload) {
    try {
      const response = await resolveConflict(transactionId, resolutionPayload);
      if (response.success) {
        await deleteItem(SYNC_QUEUE_STORE, transactionId);
        console.log("Conflict resolved and removed from queue.", transactionId);
        return { success: true };
      } else {
        console.error("Failed to resolve conflict on server:", response.message);
        return { success: false, message: response.message };
      }
    } catch (err) {
      console.error("Error resolving conflict:", err);
      return { success: false, message: err.message };
    }
  }
}

export default SyncManager;
