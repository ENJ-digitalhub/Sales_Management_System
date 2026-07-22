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
  if (!btn || navigator.userAgent.includes("Electron")) return;

  btn.addEventListener("click", async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      deferredPrompt = null;
      btn.hidden = true;
    } else {
      showManualInstallInstructions();
    }
  });

  if (deferredPrompt) btn.hidden = false; // in case the event already fired
}

function showManualInstallInstructions() {
  const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  const msg = isIOS
    ? "To install: tap Share, then \"Add to Home Screen.\""
    : "To install: open your browser menu, then \"Add to Home Screen\" or \"Install App.\"";
  alert(msg);
}