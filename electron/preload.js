// electron/preload.js
// Intentionally minimal — the frontend is plain vanilla JS talking to the
// backend over HTTP (see frontend/services/api.js), so no IPC bridge is
// needed. This file exists as a safe, empty contextIsolation boundary.