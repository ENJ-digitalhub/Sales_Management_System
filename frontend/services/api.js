/* ==========================================================================
   api.js — Fetch wrapper for Sales Management System.
   All API calls go through here. Token handling is delegated entirely
   to auth.js — this file never touches localStorage directly.
   ========================================================================== */

import { getToken, logout } from '../modules/auth.js';

const BASE_URL = 'http://127.0.0.1:5000';

/**
 * Core fetch wrapper. Attaches the auth token via auth.js if available.
 * On a 401, the session is no longer valid (expired, or device logged
 * out elsewhere) — clear it and send the user back to login.
 */
async function request(method, path, body = null) {
  const headers = {
    'Content-Type': 'application/json',
  };

  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const options = { method, headers };
  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${BASE_URL}${path}`, options);
  const data = await response.json();

  if (response.status === 401) {
    await logout();
    window.location.href = '../pages/login.html';
    throw { status: 401, data };
  }

  if (!response.ok) {
    throw { status: response.status, data };
  }

  return data;
}

/* ---------- Convenience methods ---------- */
const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, body),
  patch: (path, body) => request('PATCH', path, body),
  delete: (path) => request('DELETE', path),
};

/* ---------- Products ---------- */
const ProductsAPI = {
  getAll: () => api.get('/products'),
};

export { api, ProductsAPI };