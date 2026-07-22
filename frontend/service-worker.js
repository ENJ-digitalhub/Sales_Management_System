// frontend/service-worker.js
//
// Caches the static app shell only. Never caches API responses —
// this app has no offline data sync yet (see docs/ARCHITECTURE_CURRENT.md).
// Serving stale stock/price data would be worse than a network error.
const CACHE_NAME = "txretailos-shell-v1";

const ASSETS = [
  "/",
  "/manifest.json",
  "/assets/styles.css",
  "/pages/login.html",
];

// Backend blueprint prefixes — request paths starting with these are
// always fetched live, never intercepted by the cache.
const API_PREFIXES = [
  "/auth", "/items", "/sales", "/purchases",
  "/reports", "/sync", "/conflicts", "/health",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  if (API_PREFIXES.some((p) => url.pathname.startsWith(p))) return;
  if (event.request.method !== "GET") return;

  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});