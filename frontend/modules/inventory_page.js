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
  });
}

loadProducts();