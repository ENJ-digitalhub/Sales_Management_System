/* ==========================================================================
   RetailOS — Landing Page Behaviour
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
     --------------------------------------------------------------------- */
  emailjs.init('oNZdWmbCiQOiu5Kgu');

  var betaForm = document.getElementById('betaForm');
  var formSuccess = document.getElementById('formSuccess');

  if (betaForm) {
    betaForm.addEventListener('submit', function (e) {
      e.preventDefault();

      var storeName = document.getElementById('storeName');
      var contactInfo = document.getElementById('contactInfo');
      var willingPay = document.getElementById('willingPay');

      var valid = storeName.value.trim() && contactInfo.value.trim() && willingPay.value.trim();
      if (!valid) { betaForm.reportValidity(); return; }

      var submitBtn = betaForm.querySelector('[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Sending...';

      emailjs.send('service_zh2141t', 'template_6ysnzme', {
        store_name: storeName.value.trim(),
        contact_info: contactInfo.value.trim(),
        willing_pay: willingPay.value.trim(),
        submitted_at: new Date().toLocaleString()
      })
        .then(function () {
          betaForm.reset();
          betaForm.hidden = true;
          if (formSuccess){
            submitBtn.textContent = 'Sent'
            formSuccess.hidden = false;
          } 
        })
        .catch(function (err) {
          console.error('EmailJS error:', err);
          submitBtn.disabled = false;
          submitBtn.textContent = 'Request a beta spot';
          alert('Something went wrong. Please try again.');
        });
    });
  }

  /* ---------------------------------------------------------------------
     4. Screenshot carousel
     --------------------------------------------------------------------- */
  var gallery = document.querySelector('.shot-gallery');
  var shotTrack = document.querySelector('.shot-track');
  var shotSlides = document.querySelectorAll('.shot');
  var shotDotsContainer = document.getElementById('shotDots');
  var shotPrev = document.getElementById('shotPrev');
  var shotNext = document.getElementById('shotNext');
  var shotIndex = 0;
  var shotTotal = shotSlides.length;
  var shotTimer = null;

  if (shotTrack && shotTotal > 0) {

    // Build dots
    shotSlides.forEach(function (_, i) {
      var dot = document.createElement('button');
      dot.className = 'shot-dot' + (i === 0 ? ' is-active' : '');
      dot.setAttribute('aria-label', 'Go to slide ' + (i + 1));
      dot.addEventListener('click', function () { goToShot(i); resetShotTimer(); });
      shotDotsContainer.appendChild(dot);
    });

    function updateShot() {
      shotTrack.style.transform = 'translateX(-' + (shotIndex * 100) + '%)';
      document.querySelectorAll('.shot-dot').forEach(function (d, i) {
        d.classList.toggle('is-active', i === shotIndex);
      });
    }

    function goToShot(n) {
      shotIndex = (n + shotTotal) % shotTotal;
      updateShot();
    }

    function nextShot() { goToShot(shotIndex + 1); }
    function prevShot() { goToShot(shotIndex - 1); }

    function resetShotTimer() {
      clearInterval(shotTimer);
      shotTimer = setInterval(nextShot, 5000);
    }

    if (shotPrev) shotPrev.addEventListener('click', function () { prevShot(); resetShotTimer(); });
    if (shotNext) shotNext.addEventListener('click', function () { nextShot(); resetShotTimer(); });

    resetShotTimer();
  }
})();