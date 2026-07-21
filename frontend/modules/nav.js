// frontend/modules/nav.js
// Single source of truth for sidebar navigation across every page.
// Only links to backend-supported pages are active; unsupported ones carry a "Soon" badge.

import { getCurrentUser } from './auth.js';

const ICONS = {
  'sales.html': `<svg viewBox="0 0 24 24" class="nav-icon" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="8" cy="21" r="1"/>
  <circle cx="19" cy="21" r="1"/>
  <path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/>
</svg>`,

};

const COMMON = [
  { href: 'sales.html', label: 'Sales', icon: '../assets/icons/sales.svg' },
  { href: 'items.html', label: 'Products', icon: '../assets/icons/products.svg' },
  { href: 'inventory.html', label: 'Inventory', icon: '../assets/icons/inventory.svg' },
  { href: 'transactions.html', label: 'Transactions', icon: '../assets/icons/transactions.svg' },
];

const MANAGER_EXTRA = [
  { href: 'purchases.html', label: 'Purchases', icon: '../assets/icons/purchases.svg' },
  { href: 'report.html', label: 'Reports', icon: '../assets/icons/reports.svg' },
];

const ADMIN_EXTRA = [
  { href: 'purchases.html', label: 'Purchases', icon: '../assets/icons/purchases.svg' },
  { href: 'report.html', label: 'Reports', icon: '../assets/icons/reports.svg' },
  { href: 'users.html', label: 'Users', icon: '../assets/icons/users.svg', comingSoon: true },
];

const SYSTEM = [
  { href: 'notification.html', label: 'Notifications', icon: '../assets/icons/notifications.svg', comingSoon: true },
  { href: 'settings.html', label: 'Settings', icon: '../assets/icons/settings.svg' },
];

function dashboardHref(role) {
  if (role === 'admin') return 'admin_dashboard.html';
  if (role === 'manager') return 'manager_dashboard.html';
  return 'employee_dashboard.html';
}

function link({ href, label, icon, comingSoon }, active) {
  const cls = active ? ' class="active-link"' : '';
  const badge = comingSoon ? ' <span class="badge-soon">Soon</span>' : '';

  return `
    <a href="${href}"${cls}>
      <span class="sidebar-icon" style="--icon-url: url('${icon}')"></span>
      <span class="label">${label}</span>
      ${badge}
    </a>
  `;
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

  const storeLinks = [
    { href: dashboardHref(role), label: 'Dashboard', icon: '../assets/icons/dashboard.svg' },
    ...COMMON
  ];
  if (role === 'manager') storeLinks.push(...MANAGER_EXTRA);
  if (role === 'admin') storeLinks.push(...ADMIN_EXTRA);

  sidebar.innerHTML = `
    <div class="store-section">
      <button id="storeToggle" class="store-btn">My Store ▾</button>
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