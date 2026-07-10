<<<<<<< HEAD
// frontend/modules/inventory_page.js
import { getCurrentUser, requireAuth } from "./auth.js";
import { getProducts, createProduct, editProduct, deactivateProduct } from "./inventory.js";

requireAuth();

const LOW_STOCK_THRESHOLD = 5;
const currentUser = getCurrentUser();
const canManage = currentUser && (currentUser.role === "admin" || currentUser.role === "manager");

let products = [];

async function loadProducts() {
  const { ok, data } = await getProducts();
  if (!ok) {
    alert(data.message || "Failed to load products");
    return;
  }
  products = data.products;
  render();
}

function render() {
  renderTable();
  renderLowStockBanner();
}

function renderTable() {
  const tbody = document.getElementById("product-table-body");
  tbody.innerHTML = "";

  document.getElementById("actions-header").style.display = canManage ? "" : "none";
  document.getElementById("add-product-section").style.display = canManage ? "" : "none";

  for (const product of products) {
    const row = document.createElement("tr");
    const isLowStock = product.stock_quantity <= LOW_STOCK_THRESHOLD;

    if (isLowStock) {
      row.classList.add("low-stock-row"); // amber highlight via CSS class
    }

    row.innerHTML = `
      <td>${product.name}</td>
      <td>${product.category || "-"}</td>
      <td>${product.selling_price.toFixed(2)}</td>
      <td>${product.cost_price.toFixed(2)}</td>
      <td>${product.stock_quantity}${isLowStock ? " ⚠️" : ""}</td>
    `;

    if (canManage) {
      const actionsCell = document.createElement("td");

      const editBtn = document.createElement("button");
      editBtn.textContent = "Edit";
      editBtn.addEventListener("click", () => openEditPrompt(product));

      const deleteBtn = document.createElement("button");
      deleteBtn.textContent = "Delete";
      deleteBtn.addEventListener("click", () => confirmDeactivate(product));

      actionsCell.appendChild(editBtn);
      actionsCell.appendChild(deleteBtn);
      row.appendChild(actionsCell);
    }

    tbody.appendChild(row);
  }
}

function renderLowStockBanner() {
  const banner = document.getElementById("low-stock-banner");
  const lowStockCount = products.filter((p) => p.stock_quantity <= LOW_STOCK_THRESHOLD).length;

  if (lowStockCount > 0) {
    banner.style.display = "inline";
    banner.textContent = `⚠️ ${lowStockCount} product(s) low on stock`;
  } else {
    banner.style.display = "none";
  }
}

async function openEditPrompt(product) {
  const newStock = prompt(`New stock quantity for ${product.name}:`, product.stock_quantity);
  if (newStock === null) return;

  const qty = parseInt(newStock, 10);
  if (isNaN(qty) || qty < 0) {
    alert("Invalid quantity");
    return;
  }

  const { ok, data } = await editProduct(product.id, { stock_quantity: qty });
  if (!ok) {
    alert(data.message || "Failed to update product");
    return;
  }
  await loadProducts();
}

async function confirmDeactivate(product) {
  const confirmed = confirm(`Deactivate "${product.name}"? It will be hidden from the product list.`);
  if (!confirmed) return;

  const { ok, data } = await deactivateProduct(product.id);
  if (!ok) {
    alert(data.message || "Failed to deactivate product");
    return;
  }
  await loadProducts();
}

if (canManage) {
  document.getElementById("add-product-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const fields = {
      name: document.getElementById("new-name").value.trim(),
      category: document.getElementById("new-category").value.trim() || null,
      selling_price: parseFloat(document.getElementById("new-selling-price").value),
      cost_price: parseFloat(document.getElementById("new-cost-price").value),
      stock_quantity: parseInt(document.getElementById("new-stock").value, 10),
    };

    if (!fields.name || isNaN(fields.selling_price) || isNaN(fields.cost_price) || isNaN(fields.stock_quantity)) {
      alert("Please fill in all required fields correctly");
      return;
    }

    const { ok, data } = await createProduct(fields);
    if (!ok) {
      alert(data.message || "Failed to create product");
      return;
    }

    e.target.reset();
    await loadProducts();
=======
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
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
  });
}

loadProducts();