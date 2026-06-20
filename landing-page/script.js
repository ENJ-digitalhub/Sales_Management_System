/* ==========================================================================
   LocalLedger — Landing Page Behaviour
   No frameworks. Three jobs: mobile nav, the hero sync console demo,
   and the beta signup form.
   ========================================================================== */

(function () {
  'use strict';

  /* ---------------------------------------------------------------------
     1. Mobile nav toggle
     --------------------------------------------------------------------- */
  var header = document.getElementById('siteHeader');
  var navToggle = document.getElementById('navToggle');
  var mainNav = document.getElementById('mainNav');

  if (navToggle && header) {
    navToggle.addEventListener('click', function () {
      var isOpen = header.classList.toggle('nav-open');
      navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    // Close the mobile menu after a nav link is tapped.
    mainNav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        header.classList.remove('nav-open');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ---------------------------------------------------------------------
     2. Hero "sync console" — demonstrates offline-first behaviour
        described in the product docs: sales queue locally while
        offline (PENDING_SYNC) and flip to synced once reconnected.
     --------------------------------------------------------------------- */
  var consoleLog = document.getElementById('consoleLog');
  var statusPill = document.getElementById('statusPill');
  var wifiToggle = document.getElementById('wifiToggle');

  var SAMPLE_ITEMS = [
    { name: 'Indomie Carton', price: '₦5,200' },
    { name: 'Peak Milk 400g', price: '₦1,650' },
    { name: 'Coca-Cola 50cl', price: '₦400' },
    { name: 'Golden Morn 900g', price: '₦2,300' },
    { name: 'Bread Loaf', price: '₦1,200' },
    { name: 'Detergent Sachet', price: '₦350' },
    { name: 'Rice 1 Paint', price: '₦2,100' }
  ];

  var isOnline = true;
  var pendingCount = 0;
  var maxLines = 7;
  var tickTimer = null;
  var saleCounter = 1024;

  function pad(n) {
    return n.toString().padStart(4, '0');
  }

  function randomItem() {
    return SAMPLE_ITEMS[Math.floor(Math.random() * SAMPLE_ITEMS.length)];
  }

  function addLine(text, kind) {
    if (!consoleLog) return;
    var line = document.createElement('div');
    line.className = 'console-line ' + (kind || '');

    var tag = document.createElement('span');
    tag.className = 'tag';
    tag.textContent = kind === 'ok' ? '✓' : kind === 'pending' ? '⏳' : '⚠';

    var msg = document.createElement('span');
    msg.textContent = text;

    line.appendChild(tag);
    line.appendChild(msg);
    consoleLog.appendChild(line);

    while (consoleLog.children.length > maxLines) {
      consoleLog.removeChild(consoleLog.firstChild);
    }
    consoleLog.scrollTop = consoleLog.scrollHeight;
  }

  function setStatus(online) {
    isOnline = online;
    if (!statusPill) return;
    if (online) {
      statusPill.textContent = '● ONLINE';
      statusPill.classList.remove('is-offline');
      statusPill.classList.add('is-online');
    } else {
      statusPill.textContent = '● OFFLINE';
      statusPill.classList.remove('is-online');
      statusPill.classList.add('is-offline');
    }
  }

  function simulateSale() {
    var item = randomItem();
    saleCounter += 1;
    var label = 'Sale #' + pad(saleCounter % 10000) + ' — ' + item.name + ' (' + item.price + ')';

    if (isOnline) {
      addLine(label + ' synced', 'ok');
    } else {
      pendingCount += 1;
      addLine(label + ' queued (PENDING_SYNC)', 'pending');
    }
  }

  function goOffline() {
    setStatus(false);
    addLine('Connection lost — switching to local offline queue', 'warn');
  }

  function goOnline() {
    setStatus(true);
    if (pendingCount > 0) {
      addLine('Reconnected — syncing ' + pendingCount + ' queued sale' + (pendingCount === 1 ? '' : 's') + '...', 'warn');
      var toSync = pendingCount;
      pendingCount = 0;
      for (var i = 0; i < toSync; i++) {
        (function (idx) {
          setTimeout(function () {
            addLine('Queued sale ' + (idx + 1) + ' of ' + toSync + ' synced', 'ok');
          }, 280 * (idx + 1));
        })(i);
      }
    } else {
      addLine('Reconnected to store PC', 'ok');
    }
  }

  if (wifiToggle) {
    wifiToggle.addEventListener('click', function () {
      if (isOnline) {
        goOffline();
        wifiToggle.textContent = 'Restore connection';
      } else {
        goOnline();
        wifiToggle.textContent = 'Simulate Wi-Fi drop';
      }
    });
  }

  function tick() {
    simulateSale();
  }

  function startConsole() {
    addLine('Connected to STORE-PC on local network', 'ok');
    addLine('Product list synced — 142 items', 'ok');
    tickTimer = setInterval(tick, 2600);
  }

  if (consoleLog) {
    startConsole();
  }

  /* ---------------------------------------------------------------------
     3. Beta signup form
        This is a static landing page with no backend wired up yet.
        Replace the block marked below with a real submission
        (e.g. POST to your /sync or signup endpoint) when one exists.
     --------------------------------------------------------------------- */
  var betaForm = document.getElementById('betaForm');
  var formSuccess = document.getElementById('formSuccess');

  if (betaForm) {
    betaForm.addEventListener('submit', function (e) {
      e.preventDefault();

      var storeName = document.getElementById('storeName');
      var contactInfo = document.getElementById('contactInfo');
      var willingPay = document.getElementById('willingPay');

      var valid = storeName.value.trim() && contactInfo.value.trim() && willingPay.value.trim();
      if (!valid) {
        betaForm.reportValidity();
        return;
      }

      // --- Wire this up to a real endpoint when one is available ---
      var submission = {
        storeName: storeName.value.trim(),
        contactInfo: contactInfo.value.trim(),
        willingPay: willingPay.value.trim(),
        submittedAt: new Date().toISOString()
      };
      console.log('Beta signup captured (no backend wired yet):', submission);
      // ---------------------------------------------------------------

      betaForm.hidden = true;
      if (formSuccess) formSuccess.hidden = false;
    });
  }
})();
