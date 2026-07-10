<<<<<<< HEAD
// frontend/modules/purchases_page.js
import { getCurrentUser, requireAuth, BASE_URL, getToken } from "./auth.js";
import { getPurchaseHistory, createPurchase, approvePurchase } from "./purchases.js";

requireAuth();

const currentUser = getCurrentUser();
const canCreatePurchase = currentUser && (currentUser.role === "admin" || currentUser.role === "manager");
const canApprove = currentUser && currentUser.role === "admin"; // approval is admin-only, stricter than create

let products = [];
let purchaseItems = []; // [{ product_id, name, quantity, cost_price }]

async function loadProductsForDropdown() {
  const response = await fetch(`${BASE_URL}/products`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  const data = await response.json();
  products = data.products || [];

  const select = document.getElementById("purchase-product");
  select.innerHTML = products
    .map((p) => `<option value="${p.id}">${p.name}</option>`)
    .join("");
}

function renderPurchaseItemsList() {
  const list = document.getElementById("purchase-items-list");
  list.innerHTML = "";

  for (const item of purchaseItems) {
    const li = document.createElement("li");
    li.textContent = `${item.name} — qty ${item.quantity} @ ${item.cost_price.toFixed(2)} each`;
    list.appendChild(li);
  }
}

async function loadPurchaseHistory() {
  const { ok, data } = await getPurchaseHistory();
  if (!ok) {
    alert(data.message || "Failed to load purchase history");
    return;
  }
  renderPurchaseTable(data.purchases);
}

function renderPurchaseTable(purchases) {
  const tbody = document.getElementById("purchase-table-body");
  tbody.innerHTML = "";

  document.getElementById("approve-header").style.display = canApprove ? "" : "none";
  document.getElementById("new-purchase-section").style.display = canCreatePurchase ? "" : "none";

  for (const purchase of purchases) {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${purchase.id.slice(0, 8)}...</td>
      <td>${purchase.supplier || "-"}</td>
      <td>${purchase.total_cost.toFixed(2)}</td>
      <td>${purchase.status}</td>
      <td>${new Date(purchase.created_at).toLocaleString()}</td>
    `;

    if (canApprove) {
      const actionCell = document.createElement("td");
      if (purchase.status === "pending") {
        const approveBtn = document.createElement("button");
        approveBtn.textContent = "Approve";
        approveBtn.addEventListener("click", () => handleApprove(purchase.id));
        actionCell.appendChild(approveBtn);
      } else {
        actionCell.textContent = "-";
      }
      row.appendChild(actionCell);
    }

    tbody.appendChild(row);
  }
}

async function handleApprove(purchaseId) {
  const confirmed = confirm("Approve this purchase? Stock will be updated immediately.");
  if (!confirmed) return;

  const { ok, data } = await approvePurchase(purchaseId);
  if (!ok) {
    alert(data.message || "Failed to approve purchase");
    return;
  }
  alert(data.message);
  await loadPurchaseHistory();
}

if (canCreatePurchase) {
  document.getElementById("add-item-btn").addEventListener("click", () => {
    const productSelect = document.getElementById("purchase-product");
    const productId = productSelect.value;
    const product = products.find((p) => p.id === productId);
    const quantity = parseInt(document.getElementById("purchase-quantity").value, 10);
    const costPrice = parseFloat(document.getElementById("purchase-cost").value);

    if (!product) {
      alert("Select a product");
      return;
    }
    if (!quantity || quantity <= 0) {
      alert("Enter a valid quantity");
      return;
    }
    if (isNaN(costPrice) || costPrice < 0) {
      alert("Enter a valid cost price");
      return;
    }

    purchaseItems.push({
      product_id: product.id,
      name: product.name,
      quantity,
      cost_price: costPrice,
    });

    renderPurchaseItemsList();

    document.getElementById("purchase-quantity").value = "";
    document.getElementById("purchase-cost").value = "";
  });

  document.getElementById("purchase-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    if (purchaseItems.length === 0) {
      alert("Add at least one item to the purchase");
      return;
    }

    const supplier = document.getElementById("purchase-supplier").value.trim();

    const { ok, data } = await createPurchase({
      items: purchaseItems.map((i) => ({
        product_id: i.product_id,
        quantity: i.quantity,
        cost_price: i.cost_price,
      })),
      supplier,
    });

    if (!ok) {
      alert(data.message || "Failed to create purchase");
      return;
    }

    alert("Purchase created — pending approval.");
    purchaseItems = [];
    renderPurchaseItemsList();
    e.target.reset();
    await loadPurchaseHistory();
  });
}

async function init() {
  if (canCreatePurchase) {
    await loadProductsForDropdown();
  }
  await loadPurchaseHistory();
}

init();
=======
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
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
