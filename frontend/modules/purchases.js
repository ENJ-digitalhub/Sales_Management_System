// frontend/modules/purchases.js
import { getToken, BASE_URL } from "./auth.js";

async function _authedFetch(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
      ...(options.headers || {}),
    },
  });
  const data = await response.json();
  return { ok: response.ok, status: response.status, data };
}

export async function getPurchaseHistory() {
  return _authedFetch("/purchases/history");
}

export async function createPurchase({ items, supplier }) {
  return _authedFetch("/purchases", {
    method: "POST",
    body: JSON.stringify({ items, supplier: supplier || null }),
  });
}

export async function approvePurchase(purchaseId) {
  return _authedFetch(`/purchases/${purchaseId}/approve`, {
    method: "POST",
  });
}