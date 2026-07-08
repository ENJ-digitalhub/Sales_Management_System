// frontend\modules\inventory_page.js
import { requireAuth, getCurrentUser } from './auth.js';
import { getProducts, createProduct, updateProduct, deleteProduct } from '../services/api.js';

requireAuth();
const user = getCurrentUser();
const canManage = user && (user.role === 'admin' || user.role === 'manager');

const tableBody = document.getElementById('product-table-body');
const actionsHeader = document.getElementById('actions-header');
const addSection = document.getElementById('add-product-section');
const addForm = document.getElementById('add-product-form');
const lowStockBanner = document.getElementById('low-stock-banner');

if (canManage) {
  actionsHeader.style.display = '';
  addSection.style.display = '';
}

let products = [];

function render() {
  const hasLowStock = products.some(p => p.stock_quantity <= 5);
  lowStockBanner.style.display = hasLowStock ? '' : 'none';
  lowStockBanner.textContent = hasLowStock ? '⚠ Some products are low on stock' : '';

  tableBody.innerHTML = products.map(p => `
    <tr>
      <td>${p.name}</td>
      <td>${p.category || '-'}</td>
      <td>₦${Number(p.selling_price).toLocaleString()}</td>
      <td>₦${Number(p.cost_price).toLocaleString()}</td>
      <td class="${p.stock_quantity <= 5 ? 'stock-low' : ''}">${p.stock_quantity}</td>
      ${canManage ? `
      <td>
        <button data-edit="${p.id}">Edit</button>
        <button data-delete="${p.id}">Delete</button>
      </td>` : ''}
    </tr>
  `).join('');

  if (canManage) {
    tableBody.querySelectorAll('[data-edit]').forEach(btn => {
      btn.addEventListener('click', () => editProduct(btn.dataset.edit));
    });
    tableBody.querySelectorAll('[data-delete]').forEach(btn => {
      btn.addEventListener('click', () => removeProduct(btn.dataset.delete));
    });
  }
}

async function loadProducts() {
  const data = await getProducts();
  products = data.products || [];
  render();
}

async function editProduct(productId) {
  const product = products.find(p => p.id === productId);
  if (!product) return;

  const name = prompt('Name', product.name) ?? product.name;
  const sellingPrice = prompt('Selling price', product.selling_price) ?? product.selling_price;
  const costPrice = prompt('Cost price', product.cost_price) ?? product.cost_price;
  const stock = prompt('Stock quantity', product.stock_quantity) ?? product.stock_quantity;

  try {
    await updateProduct(productId, {
      name,
      selling_price: sellingPrice,
      cost_price: costPrice,
      stock_quantity: Number(stock),
    });
    await loadProducts();
  } catch (err) {
    alert(err.message || 'Failed to update product');
  }
}

async function removeProduct(productId) {
  if (!confirm('Deactivate this product?')) return;
  try {
    await deleteProduct(productId);
    await loadProducts();
  } catch (err) {
    alert(err.message || 'Failed to delete product');
  }
}

if (canManage && addForm) {
  addForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      await createProduct({
        name: document.getElementById('new-name').value,
        category: document.getElementById('new-category').value || null,
        selling_price: document.getElementById('new-selling-price').value,
        cost_price: document.getElementById('new-cost-price').value,
        stock_quantity: Number(document.getElementById('new-stock').value),
      });
      addForm.reset();
      await loadProducts();
    } catch (err) {
      alert(err.message || 'Failed to add product');
    }
  });
}

loadProducts();