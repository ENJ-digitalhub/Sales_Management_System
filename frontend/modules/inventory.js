// frontend/modules/inventory.js
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

export async function getProducts(includeInactive = false) {
  const query = includeInactive ? "?include_inactive=true" : "";
  return _authedFetch(`/products${query}`);
}

export async function createProduct(fields) {
  return _authedFetch("/products", {
    method: "POST",
    body: JSON.stringify(fields),
  });
}

export async function editProduct(productId, fields) {
  return _authedFetch(`/products/${productId}`, {
    method: "PATCH",
    body: JSON.stringify(fields),
  });
}

export async function deactivateProduct(productId) {
  return _authedFetch(`/products/${productId}`, {
    method: "DELETE",
  });
}