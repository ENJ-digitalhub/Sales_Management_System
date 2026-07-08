
import { openDB } from 'idb';

const DB_NAME = 'sales_management_db';
const DB_VERSION = 1;

const initDb = async () => {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains('products')) {
        db.createObjectStore('products', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('sales')) {
        db.createObjectStore('sales', { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains('sync_queue')) {
        db.createObjectStore('sync_queue', { keyPath: 'transaction_id' });
      }
      // Add other object stores as needed
    },
  });
};

export const getStore = async (storeName, mode) => {
  const db = await initDb();
  return db.transaction(storeName, mode).objectStore(storeName);
};

export const getAllItems = async (storeName) => {
  const store = await getStore(storeName, 'readonly');
  return store.getAll();
};

export const getItem = async (storeName, id) => {
  const store = await getStore(storeName, 'readonly');
  return store.get(id);
};

export const addItem = async (storeName, item) => {
  const store = await getStore(storeName, 'readwrite');
  return store.add(item);
};

export const putItem = async (storeName, item) => {
  const store = await getStore(storeName, 'readwrite');
  return store.put(item);
};

export const deleteItem = async (storeName, id) => {
  const store = await getStore(storeName, 'readwrite');
  return store.delete(id);
};

export const clearStore = async (storeName) => {
  const store = await getStore(storeName, 'readwrite');
  return store.clear();
};
