// frontend\modules\inventory_page.js
import { requireAuth, getCurrentUser, logout } from './auth.js';
import { renderSidebar } from './nav.js';
import { getItems, createItem, updateItem, deleteItem } from '../services/api.js';

requireAuth();
const user = getCurrentUser();
const canManage = user && (user.role === 'admin' || user.role === 'manager');

document.getElementById('userInfo').textContent = user ? `${user.name} (${user.role})` : '';
document.getElementById('logoutBtn').addEventListener('click', async () => {
  await logout();
  window.location.href = 'login.html';
});
renderSidebar('inventory.html');
document.getElementById('menuToggle').onclick = () =>
  document.getElementById('sidebar').classList.toggle('collapsed');

// Notifications (shared shell — no new functionality)
document.getElementById('notifBtn').onclick = () =>
  document.getElementById('notifModal').classList.remove('hidden');
document.getElementById('closeNotif').onclick = () =>
  document.getElementById('notifModal').classList.add('hidden');

const tableBody = document.getElementById('item-table-body');
const actionsHeader = document.getElementById('actions-header');
const addSection = document.getElementById('add-item-section');
const addServiceNote = document.getElementById('add-service-note');
const addForm = document.getElementById('add-item-form');
const lowStockBanner = document.getElementById('low-stock-banner');

let items = [];
let activeTab = 'product';

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeTab = btn.dataset.tab;
    render();
  });
});

function updateSectionVisibility() {
  if (!canManage) return;
  addSection.style.display = activeTab === 'product' ? '' : 'none';
  addServiceNote.style.display = activeTab === 'service' ? '' : 'none';
}

function render() {
  updateSectionVisibility();
  const filtered = items.filter(p => (p.type || 'product') === activeTab);

  const hasLowStock = filtered.some(p => p.stock_quantity !== null && p.stock_quantity <= 5);
  lowStockBanner.style.display = hasLowStock ? '' : 'none';
  lowStockBanner.textContent = hasLowStock ? '⚠ Some items are low on stock' : '';

  tableBody.innerHTML = filtered.map(p => `
    <tr>
      <td>${p.name}</td>
      <td>${p.category || '-'}</td>
      <td>₦${Number(p.selling_price).toLocaleString()}</td>
      <td>₦${Number(p.cost_price).toLocaleString()}</td>
      <td class="${p.stock_quantity !== null && p.stock_quantity <= 5 ? 'stock-low' : ''}">${p.stock_quantity ?? '-'}</td>
      ${canManage ? `
      <td>
        <button class="icon-btn" data-edit="${p.id}">Edit</button>
        <button class="icon-btn" data-delete="${p.id}">Delete</button>
      </td>` : ''}
    </tr>
  `).join('') || `<tr><td colspan="6" class="text-muted">No ${activeTab}s found</td></tr>`;

  if (canManage) {
    tableBody.querySelectorAll('[data-edit]').forEach(btn => {
      btn.addEventListener('click', () => editItem(btn.dataset.edit));
    });
    tableBody.querySelectorAll('[data-delete]').forEach(btn => {
      btn.addEventListener('click', () => removeItem(btn.dataset.delete));
    });
  }
}

if (canManage) actionsHeader.style.display = '';

async function loadItems() {
  const data = await getItems();
  items = data.items || [];
  render();
}

async function editItem(itemId) {
  const item = items.find(p => p.id === itemId);
  if (!item) return;

  const name = prompt('Name', item.name) ?? item.name;
  const sellingPrice = prompt('Selling price', item.selling_price) ?? item.selling_price;
  const costPrice = prompt('Cost price', item.cost_price) ?? item.cost_price;
  const stock = prompt('Stock quantity', item.stock_quantity) ?? item.stock_quantity;

  try {
    await updateItem(itemId, {
      name,
      selling_price: sellingPrice,
      cost_price: costPrice,
      stock_quantity: Number(stock),
    });
    await loadItems();
  } catch (err) {
    alert(err.message || 'Failed to update item');
  }
}

async function removeItem(itemId) {
  if (!confirm('Deactivate this item?')) return;
  try {
    await deleteItem(itemId);
    await loadItems();
  } catch (err) {
    alert(err.message || 'Failed to delete item');
  }
}

if (canManage && addForm) {
  addForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await createItem({
        name: document.getElementById('new-name').value,
        category: document.getElementById('new-category').value || null,
        selling_price: document.getElementById('new-selling-price').value,
        cost_price: document.getElementById('new-cost-price').value,
        stock_quantity: Number(document.getElementById('new-stock').value),
      });
      addForm.reset();
      await loadItems();
    } catch (err) {
      alert(err.message || 'Failed to add item');
    }
  });
}

loadItems();