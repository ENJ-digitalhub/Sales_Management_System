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