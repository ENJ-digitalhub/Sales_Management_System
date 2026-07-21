// frontend/modules/pwa.js
// Shared PWA install logic — imported by any page with an
// #installBtn element in its topbar (see nav pages below).

let deferredPrompt = null;

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/service-worker.js").catch((err) => {
    // Expected to fail on plain-HTTP LAN access — not a bug, see comment
    // in service-worker.js registration blocker notes.
    console.warn("Service worker registration skipped:", err.message);
  });
}

window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredPrompt = e;
  const btn = document.getElementById("installBtn");
  if (btn) btn.hidden = false;
});

export function wireInstallButton() {
  const btn = document.getElementById("installBtn");
  if (!btn) return;
  // Already a desktop app inside Electron — installing a PWA on top is meaningless.
  if (navigator.userAgent.includes("Electron")) return;
  btn.addEventListener("click", async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    btn.hidden = true;
  });
}