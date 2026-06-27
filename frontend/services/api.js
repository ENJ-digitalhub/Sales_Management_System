
/* ==========================================================================
   api.js — Fetch wrapper for Sales Management System
   All API calls go through here. Base URL auto-detects from current host
   so it works on localhost in dev and on LAN IP in production.
   ========================================================================== */

const BASE_URL = `${window.location.protocol}//${window.location.host}`;

/**
 * Core fetch wrapper.
 * Attaches auth token if available.
 * Returns parsed JSON or throws an error.
 */
async function request(method, path, body = null) {
  const headers = {
    'Content-Type': 'application/json',
  };

  const token = localStorage.getItem('token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const options = {
    method,
    headers,
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${BASE_URL}${path}`, options);
  const data = await response.json();

  if (!response.ok) {
    throw { status: response.status, data };
  }

  return data;
}

/* ---------- Convenience methods ---------- */
const api = {
  get:    (path)        => request('GET',    path),
  post:   (path, body)  => request('POST',   path, body),
  patch:  (path, body)  => request('PATCH',  path, body),
  delete: (path)        => request('DELETE', path),
};

/* ---------- Products ---------- */
const ProductsAPI = {
  getAll: () => api.get('/products'),
};

export { api, ProductsAPI };