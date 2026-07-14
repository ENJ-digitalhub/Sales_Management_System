// frontend/modules/conflicts_page.js
import { requireAuth, getCurrentUser, logout } from './auth.js';
import { renderSidebar } from './nav.js';
import { getConflicts, resolveConflictItem } from '../services/api.js';

requireAuth();
const user = getCurrentUser();
document.getElementById('userInfo').textContent = user ? `${user.name} (${user.role})` : '';
document.getElementById('logoutBtn').addEventListener('click', async () => {
  await logout();
  window.location.href = 'login.html';
});

renderSidebar('conflicts.html');
document.getElementById('menuToggle').onclick = () => {
  document.getElementById('sidebar').classList.toggle('collapsed');
};

const allowed = user && (user.role === 'admin' || user.role === 'manager');
const accessDenied = document.getElementById('accessDenied');
const content = document.getElementById('conflictsContent');

if (!allowed) {
  accessDenied.hidden = false;
  content.hidden = true;
} else {
  loadConflicts();
  setInterval(loadConflicts, 30000); // matches SYNC_ENGINE conflict-review cadence
}

const CONFLICT_LABELS = {
  stock: 'Stock conflict — offline sale exceeded available stock',
  deleted_item: 'Item was deactivated before this transaction synced',
  deleted_product: 'Product was deactivated before this transaction synced',
  duplicate: 'Duplicate transaction',
};

async function loadConflicts() {
  const listEl = document.getElementById('conflictList');
  const emptyEl = document.getElementById('emptyState');
  try {
    const data = await getConflicts();
    const conflicts = data.conflicts || [];
    emptyEl.hidden = conflicts.length !== 0;

    listEl.innerHTML = conflicts.map(c => `
      <div class="card mt-2">
        <div class="flex-between">
          <strong class="text-mono">${(c.transaction_id || '').slice(0, 8)}</strong>
          <span class="status syncing">${c.status}</span>
        </div>
        <p>${CONFLICT_LABELS[c.conflict_type] || c.conflict_type || 'Unresolved conflict'}</p>
        <p class="text-faint text-mono">Device: ${c.device_id || '-'} · ${c.entity_type} · ${c.operation}</p>
        <div class="actions mt-2">
          <button class="btn btn-primary" data-approve="${c.transaction_id}">Approve</button>
          <button class="btn btn-outline" data-reject="${c.transaction_id}">Reject</button>
        </div>
        <div class="login-error mt-2" data-error="${c.transaction_id}" hidden></div>
      </div>
    `).join('');

    listEl.querySelectorAll('[data-approve]').forEach(btn =>
      btn.addEventListener('click', () => resolve(btn.dataset.approve, 'approve')));
    listEl.querySelectorAll('[data-reject]').forEach(btn =>
      btn.addEventListener('click', () => {
        const note = prompt('Reason for rejecting (optional)') || null;
        resolve(btn.dataset.reject, 'reject', note);
      }));
  } catch (err) {
    listEl.innerHTML = `<div class="login-error">Failed to load conflicts: ${err.message}</div>`;
  }
}

async function resolve(transactionId, resolution, note) {
  if (!confirm(`${resolution === 'approve' ? 'Approve' : 'Reject'} this transaction?`)) return;
  const errorEl = document.querySelector(`[data-error="${transactionId}"]`);
  try {
    await resolveConflictItem(transactionId, resolution, note);
    await loadConflicts();
  } catch (err) {
    if (errorEl) {
      errorEl.textContent = err.message || 'Failed to resolve conflict';
      errorEl.hidden = false;
    }
  }
}