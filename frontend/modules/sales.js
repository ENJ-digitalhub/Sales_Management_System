// frontend/modules/sales.js
import { getToken, BASE_URL } from "./auth.js";
import { enqueue, generateUUID } from "./queue.js";

/**
 * Attempts to create a sale online. On real network failure (not a 4xx/5xx
 * response — an actual failed fetch), falls back to the offline queue.
 */
export async function createSale({ items, paymentMethod, paymentProvider, deviceId }) {
  if (!items || items.length === 0) {
    throw new Error("Cart is empty");
  }
  for (const item of items) {
    if (!item.quantity || item.quantity <= 0) {
      throw new Error("Each item needs a positive quantity");
    }
  }

  const clientTransactionId = generateUUID();

  const payload = {
    device_id: deviceId,
    client_transaction_id: clientTransactionId,
    payment_method: paymentMethod,
    payment_provider: paymentProvider || null,
    items: items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
  };

  try {
    const response = await fetch(`${BASE_URL}/sales`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken()}`,
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      return { online: true, success: false, error: data };
    }

    return { online: true, success: true, result: data.sale };
  } catch (networkError) {
    const record = await enqueue("sale", "CREATE", payload, clientTransactionId);
    return { online: false, success: true, queued: record };
  }
}