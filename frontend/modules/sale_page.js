// frontend/modules/sale_page.js
import { getToken, getDeviceId, BASE_URL } from "./auth.js";
import { createSale } from "./sales.js";
import { refreshSyncUI } from "./sync_ui.js";

let cart = [];
let products = [];

async function fetchProducts() {
  const response = await fetch(`${BASE_URL}/sales/products`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  const data = await response.json();

  if (!response.ok) {
    alert(data.message || "Failed to load products");
    return;
  }

  products = data.items || [];
  renderProductList();
}

function renderProductList() {
  const container = document.getElementById("product-list");
  container.innerHTML = "";

  for (const product of products) {
    const row = document.createElement("div");
    row.className = "product-row";
    row.innerHTML = `
      <span>${product.name}</span>
      <span>${product.selling_price.toFixed(2)}</span>
      <span>Stock: ${product.stock_quantity}</span>
      <input type="number" min="1" value="1" class="qty-input" />
      <button class="add-btn">Add</button>
    `;

    row.querySelector(".add-btn").addEventListener("click", () => {
      const qtyInput = row.querySelector(".qty-input");
      const quantity = parseInt(qtyInput.value, 10);
      if (!quantity || quantity <= 0) {
        alert("Enter a valid quantity");
        return;
      }
      addToCart(product, quantity);
    });

    container.appendChild(row);
  }
}

function addToCart(product, quantity) {
  const existing = cart.find((i) => i.product_id === product.id);
  if (existing) {
    existing.quantity += quantity;
  } else {
    cart.push({
      product_id: product.id,
      name: product.name,
      unit_price: product.selling_price,
      quantity,
    });
  }
  renderCart();
}

function renderCart() {
  const list = document.getElementById("cart-items");
  list.innerHTML = "";
  let total = 0;

  for (const item of cart) {
    const li = document.createElement("li");
    const lineTotal = item.unit_price * item.quantity;
    total += lineTotal;
    li.textContent = `${item.name} x${item.quantity} — ${lineTotal.toFixed(2)}`;
    list.appendChild(li);
  }

  document.getElementById("cart-total").textContent = total.toFixed(2);
}

document.getElementById("submit-sale").addEventListener("click", async () => {
  if (cart.length === 0) {
    alert("Cart is empty");
    return;
  }

  const paymentMethod = document.getElementById("payment-method").value;
  const deviceId = getDeviceId();

  const outcome = await createSale({ items: cart, paymentMethod, deviceId });

  if (outcome.online && outcome.success) {
    alert(`Sale complete. Receipt: ${outcome.result.receipt_number || outcome.result.id}`);
    cart = [];
    renderCart();
    await fetchProducts();
  } else if (outcome.online && !outcome.success) {
    alert(`Sale failed: ${outcome.error.message}`);
  } else {
    alert("No connection — sale saved and will sync automatically.");
    cart = [];
    renderCart();
    await refreshSyncUI(); // <-- the fix: badge/history update immediately on queue
  }
});

fetchProducts();