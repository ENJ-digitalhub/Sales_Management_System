// frontend/modules/transactions_page.js
import { requireAuth, getCurrentUser, logout } from './auth.js';
import { renderSidebar } from './nav.js';
import { getSales, cancelSale } from '../services/api.js';

requireAuth();
const user = getCurrentUser();
const canCancel = user && (user.role === 'admin' || user.role === 'manager');

document.getElementById('userInfo').textContent = user ? `${user.name} (${user.role})` : '';
document.getElementById('logoutBtn').addEventListener('click', async () => {
  await logout();
  window.location.href = 'login.html';
});
renderSidebar('transactions.html');
document.getElementById('menuToggle').onclick = () =>
  document.getElementById('sidebar').classList.toggle('collapsed');

if (canCancel) document.getElementById('actionsHeader').style.display = '';

const tableBody = document.getElementById('txTableBody');
const searchInput = document.getElementById('searchInput');
const statusFilter = document.getElementById('statusFilter');
const methodFilter = document.getElementById('methodFilter');

let allSales = []; // GET /sales already filters to "own sales" server-side for employees

function render() {
  const q = searchInput.value.trim().toLowerCase();
  const status = statusFilter.value;
  const method = methodFilter.value;

  // Client-side filtering only — GET /sales takes no query params
  const filtered = allSales.filter(s => {
    if (q && !(s.receipt_number || '').toLowerCase().includes(q)) return false;
    if (status && s.status !== status) return false;
    if (method && s.payment_method !== method) return false;
    return true;
  });

  if (filtered.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="6" class="text-muted">No transactions found</td></tr>`;
    return;
  }

  tableBody.innerHTML = filtered.map(s => `
    <tr>
      <td class="text-mono">${new Date(s.created_at).toLocaleString()}</td>
      <td class="text-mono">${s.receipt_number}</td>
      <td>₦${Number(s.total_amount).toLocaleString()}</td>
      <td>${s.payment_method}</td>
      <td><span class="status ${s.status === 'cancelled' ? 'offline' : 'online'}">${s.status}</span></td>
      ${canCancel ? `
      <td>
        ${s.status !== 'cancelled'
          ? `<button class="icon-btn" data-cancel="${s.id}">Cancel</button>`
          : '-'}
      </td>` : ''}
    </tr>
  `).join('');

  if (canCancel) {
    tableBody.querySelectorAll('[data-cancel]').forEach(btn => {
      btn.addEventListener('click', () => handleCancel(btn.dataset.cancel));
    });
  }
}

async function handleCancel(saleId) {
  if (!confirm('Cancel this sale? Stock will be restored.')) return;
  try {
    await cancelSale(saleId);
    await loadSales();
  } catch (err) {
    alert(err.message || 'Failed to cancel sale');
  }
}

async function loadSales() {
  try {
    const data = await getSales();
    allSales = (data.sales || []).sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    render();
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="6" class="login-error">Failed to load transactions: ${err.message}</td></tr>`;
  }
}

[searchInput, statusFilter, methodFilter].forEach(el => el.addEventListener('input', render));

loadSales();