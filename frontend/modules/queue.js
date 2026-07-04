/* ==========================================================================
   queue.js — Offline queue storage (IndexedDB)
   Stores offline transactions locally.
   Record shape matches SYNC_ENGINE.md §3 exactly.
   ========================================================================== */

const DB_NAME    = 'sales_management_db';
const DB_VERSION = 1;
const STORE_NAME = 'sync_queue';

/**
 * Opens the IndexedDB database.
 * Creates the sync_queue object store on first run.
 */
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = function (event) {
      const db = event.target.result;

      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, {
          keyPath: 'transaction_id',
        });

        store.createIndex('status',      'status',      { unique: false });
        store.createIndex('entity_type', 'entity_type', { unique: false });
        store.createIndex('created_at',  'created_at',  { unique: false });
      }
    };

    request.onsuccess = (e) => resolve(e.target.result);
    request.onerror   = (e) => reject(e.target.error);
  });
}

/**
 * Generates a UUID v4 for transaction_id.
 */
function generateUUID() {
  return crypto.randomUUID();
}

/**
 * Adds a transaction record to the offline queue.
 * Record shape matches SYNC_ENGINE.md §3.
 *
 * @param {string} entity_type - e.g. 'sale'
 * @param {string} operation   - 'CREATE' | 'UPDATE' | 'DELETE'
 * @param {object} payload     - the full request body
 * @param {string|null} transaction_id - pass the same id used as the
 *   server's client_transaction_id, so the queue record and the eventual
 *   server-side sale are tied together. If omitted, one is generated here.
 */
async function enqueue(entity_type, operation, payload, transaction_id = null) {
  const db = await openDB();

  const record = {
    transaction_id: transaction_id || generateUUID(),
    entity_type,
    operation,
    payload,
    status:          'PENDING',
    retry_count:     0,
    last_attempt_at: null,
    created_at:      new Date().toISOString(),
  };

  return new Promise((resolve, reject) => {
    const tx    = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req   = store.add(record);

    req.onsuccess = () => resolve(record);
    req.onerror   = (e) => reject(e.target.error);
  });
}

/**
 * Reads all records from the queue.
 */
async function getAllQueued() {
  const db = await openDB();

  return new Promise((resolve, reject) => {
    const tx    = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const req   = store.getAll();

    req.onsuccess = (e) => resolve(e.target.result);
    req.onerror   = (e) => reject(e.target.error);
  });
}

/**
 * Reads only PENDING records from the queue.
 */
async function getPending() {
  const db = await openDB();

  return new Promise((resolve, reject) => {
    const tx    = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const index = store.index('status');
    const req   = index.getAll('PENDING');

    req.onsuccess = (e) => resolve(e.target.result);
    req.onerror   = (e) => reject(e.target.error);
  });
}

/**
 * Updates the status of a single record by transaction_id.
 *
 * @param {string} transaction_id
 * @param {string} status - 'PENDING' | 'SYNCED' | 'FAILED' | 'CONFLICT'
 * @param {boolean} incrementRetry - true when this update follows a failed attempt
 */
async function updateStatus(transaction_id, status, incrementRetry = false) {
  const db = await openDB();

  return new Promise((resolve, reject) => {
    const tx    = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req   = store.get(transaction_id);

    req.onsuccess = function (e) {
      const record = e.target.result;
      if (!record) { reject(new Error('Record not found')); return; }

      record.status          = status;
      record.last_attempt_at = new Date().toISOString();
      if (incrementRetry) {
        record.retry_count = (record.retry_count || 0) + 1;
      }

      const updateReq     = store.put(record);
      updateReq.onsuccess  = () => resolve(record);
      updateReq.onerror    = (e) => reject(e.target.error);
    };

    req.onerror = (e) => reject(e.target.error);
  });
}

/**
 * Count of PENDING records — used for the UI badge.
 */
async function getPendingCount() {
  const pending = await getPending();
  return pending.length;
}

export { enqueue, getAllQueued, getPending, updateStatus, getPendingCount, generateUUID };