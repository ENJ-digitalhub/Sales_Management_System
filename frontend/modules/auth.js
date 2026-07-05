/* ==========================================================================
   auth.js — Single source of truth for everything token-related.
   No other file should read or write localStorage directly.
   ========================================================================== */

const TOKEN_KEY = 'sms_token';
const DEVICE_ID_KEY = 'sms_device_id';
const USER_KEY = 'sms_user';

// Using BASE_URL makes it easy to switch environments later (e.g., to production)
const BASE_URL = 'http://127.0.0.1:5000';

/**
 * Returns this browser's persistent device identity, generating one
 * the first time it's needed and storing it permanently.
 */
function getDeviceId() {
  let deviceId = localStorage.getItem(DEVICE_ID_KEY);
  if (!deviceId) {
    deviceId = (crypto.randomUUID ? crypto.randomUUID() : `device-${Date.now()}-${Math.random().toString(16).slice(2)}`);
    localStorage.setItem(DEVICE_ID_KEY, deviceId);
  }
  return deviceId;
}

/**
 * Decodes a JWT payload WITHOUT verifying the signature.
 * This is safe to do client-side for reading non-sensitive claims
 * (like exp, role) but must never be trusted as proof of authenticity —
 * the server always re-verifies the signature on every request.
 */
function decodeTokenPayload(token) {
  try {
    const payloadBase64 = token.split('.')[1];
    const decoded = atob(payloadBase64.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch (err) {
    return null;
  }
}

/**
 * Logs in against the backend, stores the token + user on success.
 * Throws on failure so callers can show an error message.
 */
async function login(username, password) {
  const device_id = getDeviceId();

  // FIXED: Separated 'await' and 'fetch' & used BASE_URL
  const response = await fetch(`${BASE_URL}/auth/login`, { 
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, device_id })
  });

  const data = await response.json();

  if (!response.ok || !data.success) {
    throw new Error(data.message || 'Invalid username or password');
  }

  localStorage.setItem(TOKEN_KEY, data.token);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));

  return data.user;
}

/**
 * Logs out: tells the server to invalidate this device's session,
 * then clears local storage regardless of whether the network call
 * succeeds.
 */
async function logout() {
  const token = getToken();
  const device_id = getDeviceId();

  try {
    if (token) {
      // FIXED: Completely cleaned up and rebuilt the broken fetch layout here
      await fetch(`${BASE_URL}/auth/logout`, { 
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({ device_id })
      });
    }
  } catch (err) {
    console.warn('Logout request failed, clearing local session anyway:', err);
  } finally {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}

/** Returns the stored token, or null if none exists. */
function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/** Returns the stored user object, or null if none exists. */
function getCurrentUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

/**
 * Checks whether a token exists and is not expired, based on its
 * own `exp` claim.
 */
function isAuthenticated() {
  const token = getToken();
  if (!token) return false;

  const payload = decodeTokenPayload(token);
  if (!payload || !payload.exp) return false;

  const nowInSeconds = Date.now() / 1000;
  return payload.exp > nowInSeconds;
}

/**
 * Returns the dashboard URL appropriate for a given role.
 * Falls back to the sales dashboard for unrecognized roles.
 */
function getDashboardForRole(role) {
  switch (role) {
    case 'admin':
      return '../pages/admin-dashboard.html';
    case 'manager':
      return '../pages/manager-dashboard.html';
    case 'employee':
    default:
      return '../pages/sales-dashboard.html';
  }
}

/**
 * Call this on any page that requires a logged-in user.
 * Redirects to login immediately if not authenticated.
 */
function requireAuth() {
  if (!isAuthenticated()) {
    window.location.href = '../pages/login.html';
  }
}

export {
  login,
  logout,
  getToken,
  getCurrentUser,
  isAuthenticated,
  getDeviceId,
  getDashboardForRole,
  requireAuth,
  BASE_URL,
};