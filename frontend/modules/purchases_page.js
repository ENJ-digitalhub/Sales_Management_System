// frontend\modules\purchases_page.js
import { requireAuth, getCurrentUser } from './auth.js';
import { getProducts, createPurchase, getPurchaseHistory, approvePurchase } from '../services/api.js';

requireAuth();
const user = getCurrentUser();
const isAdmin = user && user.role === 'admin';

const newPurchaseSection = document.getElementById('new-purchase-section');
const productSelect = document.getElementById('purchase-product');
const itemsList = document.getElementById('purchase-items-list');
const purchaseForm = document.getElementById('purchase-form');
const approveHeader = document.getElementById('approve-header');
const tableBody = document.getElementById('purchase-table-body');

newPurchaseSection.style.display = ''; // any role can create purchases
if (isAdmin) approveHeader.style.display = '';

let products = [];
let cartItems = []; // { product_id, name, quantity, cost_price }

async function loadProducts() {
  const data = await getProducts();
  products = data.products || [];
  productSelect.innerHTML = products.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
}

function renderItemsList() {
  itemsList.innerHTML = cartItems.map((item, idx) => `
    <li>
      ${item.name} — qty ${item.quantity} @ ₦${item.cost_price}
      <button type="button" data-remove="${idx}">✕</button>
    </li>
  `).join('');

  itemsList.querySelectorAll('[data-remove]').forEach(btn => {
    btn.addEventListener('click', () => {
      cartItems.splice(Number(btn.dataset.remove), 1);
      renderItemsList();
    });
  });
}

document.getElementById('add-item-btn').addEventListener('click', () => {
  const productId = productSelect.value;
  const product = products.find(p => p.id === productId);
  const quantity = Number(document.getElementById('purchase-quantity').value);
  const costPrice = document.getElementById('purchase-cost').value;

  if (!product || !quantity || quantity <= 0 || !costPrice) {
    alert('Select a product, quantity, and cost price');
    return;
  }

  cartItems.push({ product_id: productId, name: product.name, quantity, cost_price: costPrice });
  renderItemsList();
  document.getElementById('purchase-quantity').value = '';
  document.getElementById('purchase-cost').value = '';
});

purchaseForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (cartItems.length === 0) {
    alert('Add at least one item');
    return;
  }

  try {
    await createPurchase({
      items: cartItems.map(({ product_id, quantity, cost_price }) => ({ product_id, quantity, cost_price })),
      supplier: document.getElementById('purchase-supplier').value || null,
    });
    cartItems = [];
    renderItemsList();
    purchaseForm.reset();
    await loadHistory();
  } catch (err) {
    alert(err.message || 'Failed to create purchase');
  }
});

async function loadHistory() {
  const data = await getPurchaseHistory();
  const purchases = data.purchases || [];

  tableBody.innerHTML = purchases.map(p => `
    <tr>
      <td>${p.id.slice(0, 8)}</td>
      <td>${p.supplier || '-'}</td>
      <td>₦${Number(p.total_cost).toLocaleString()}</td>
      <td>${p.status}</td>
      <td>${new Date(p.created_at).toLocaleString()}</td>
      ${isAdmin ? `
      <td>
        ${p.status === 'pending' ? `<button data-approve="${p.id}">Approve</button>` : '-'}
      </td>` : ''}
    </tr>
  `).join('');

  if (isAdmin) {
    tableBody.querySelectorAll('[data-approve]').forEach(btn => {
      btn.addEventListener('click', async () => {
        try {
          await approvePurchase(btn.dataset.approve);
          await loadHistory();
        } catch (err) {
          alert(err.message || 'Failed to approve purchase');
        }
      });
    });
  }
}

loadProducts();
loadHistory();