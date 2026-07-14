// frontend/modules/nav.js
// Single source of truth for sidebar navigation across every page.
// Only links to backend-supported pages are active; unsupported ones carry a "Soon" badge.

import { getCurrentUser } from './auth.js';

const COMMON = [
  { href: 'sales.html', label: 'Sales' },
  { href: 'items.html', label: 'Products' },
  { href: 'inventory.html', label: 'Inventory' },
  { href: 'transactions.html', label: 'Transactions' },
];

const MANAGER_EXTRA = [
  { href: 'purchases.html', label: 'Purchases' },
  { href: 'report.html', label: 'Reports' },
];

const ADMIN_EXTRA = [
  { href: 'purchases.html', label: 'Purchases' },
  { href: 'report.html', label: 'Reports' },
  { href: 'users.html', label: 'Users', comingSoon: true },
];

const SYSTEM = [
  { href: 'notification.html', label: 'Notifications', comingSoon: true },
  { href: 'settings.html', label: 'Settings' },
];

function dashboardHref(role) {
  if (role === 'admin') return 'admin_dashboard.html';
  if (role === 'manager') return 'manager_dashboard.html';
  return 'employee_dashboard.html';
}

function link({ href, label, comingSoon }, active) {
  const cls = active ? ' class="active-link"' : '';
  const badge = comingSoon ? ' <span class="badge-soon">Soon</span>' : '';
  return `<a href="${href}"${cls}>${label}${badge}</a>`;
}

/** Applies the saved theme preference. Pure client-side — no backend involved. */
export function applyStoredTheme() {
  const theme = localStorage.getItem('theme') || 'dark';
  document.body.classList.toggle('light-theme', theme === 'light');
}

export function renderSidebar(activeHref) {
  applyStoredTheme();

  const sidebar = document.getElementById('sidebar');
  if (!sidebar) return;

  const user = getCurrentUser();
  const role = user?.role || 'employee';

  const storeLinks = [{ href: dashboardHref(role), label: 'Dashboard' }, ...COMMON];
  if (role === 'manager') storeLinks.push(...MANAGER_EXTRA);
  if (role === 'admin') storeLinks.push(...ADMIN_EXTRA);

  sidebar.innerHTML = `
    <div class="store-section">
      <button id="storeToggle" class="store-btn">🏪 My Store ▾</button>
      <div id="storeMenu" class="store-menu">
        ${storeLinks.map(l => link(l, l.href === activeHref)).join('')}
      </div>
    </div>
    <div class="sidebar-section">
      ${SYSTEM.map(l => link(l, l.href === activeHref)).join('')}
    </div>
  `;

  document.getElementById('storeToggle').onclick = () => {
    document.getElementById('storeMenu').classList.toggle('hidden');
  };
}