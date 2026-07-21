// Install-only. No fetch/caching — this app has no offline mode yet
// (see docs/ARCHITECTURE_CURRENT.md). Do not add a fetch handler here
// until SYNC_ENABLED ships, or you risk serving stale stock/price data.
self.addEventListener("install", () => {
  self.skipWaiting();
});
self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});