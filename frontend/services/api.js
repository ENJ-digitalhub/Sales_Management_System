// frontend\services\api.js
const API_BASE_URL = window.location.origin;

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || 'Something went wrong');
  }
  return response.json();
};

export const loginUser = async (username, password, deviceName) => {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, device_name: deviceName }),
  });
  return handleResponse(response);
};

export const logoutUser = async () => {
  const response = await fetch(`${API_BASE_URL}/auth/logout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
  });
  return handleResponse(response);
};

export const verifyToken = async () => {
  const response = await fetch(`${API_BASE_URL}/auth/verify`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return response.json(); // Verify token might return {valid: false} without throwing an error
};

export const getItems = async () => {
  const response = await fetch(`${API_BASE_URL}/items`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
};

export const createItem = async (itemData) => {
  const response = await fetch(`${API_BASE_URL}/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(itemData),
  });
  return handleResponse(response);
};

export const updateItem = async (itemId, itemData) => {
  const response = await fetch(`${API_BASE_URL}/items/${itemId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(itemData),
  });
  return handleResponse(response);
};

export const deleteItem = async (itemId) => {
  const response = await fetch(`${API_BASE_URL}/items/${itemId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
};

export const createSale = async (saleData) => {
  const response = await fetch(`${API_BASE_URL}/sales`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(saleData),
  });
  return handleResponse(response);
};

export const getSales = async () => {
  const response = await fetch(`${API_BASE_URL}/sales`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
};

export const getSale = async (saleId) => {
  const response = await fetch(`${API_BASE_URL}/sales/${saleId}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
};

export const editSale = async (saleId, saleData) => {
  const response = await fetch(`${API_BASE_URL}/sales/${saleId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(saleData),
  });
  return handleResponse(response);
};

export const cancelSale = async (saleId) => {
  const response = await fetch(`${API_BASE_URL}/sales/${saleId}/cancel`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
};

export const pushChanges = async (changes) => {
  const response = await fetch(`${API_BASE_URL}/sync/push`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify({ changes }),
  });
  return handleResponse(response);
};

export const pullChanges = async (lastSyncTime) => {
  const response = await fetch(`${API_BASE_URL}/sync/pull?last_sync_time=${lastSyncTime.toISOString()}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
};

export const resolveConflict = async (transactionId, resolutionPayload) => {
  const response = await fetch(`${API_BASE_URL}/sync/resolve-conflict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify({ transaction_id: transactionId, resolution_payload: resolutionPayload }),
  });
  return handleResponse(response);
};

// --- Purchases ---
export const createPurchase = async (payload) => {
  const response = await fetch(`${API_BASE_URL}/purchases/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
};

export const getPurchaseHistory = async () => {
  const response = await fetch(`${API_BASE_URL}/purchases/history`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
};

export const approvePurchase = async (purchaseId) => {
  const response = await fetch(`${API_BASE_URL}/purchases/${purchaseId}/approve`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
};

// --- Reports ---
export const getDailyReport = async (date) => {
  const qs = date ? `?date=${date}` : '';
  const response = await fetch(`${API_BASE_URL}/reports/daily${qs}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
};

export const getMonthlyReport = async (month) => {
  const qs = month ? `?month=${month}` : '';
  const response = await fetch(`${API_BASE_URL}/reports/monthly${qs}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
};

export const getYearlyReport = async (year) => {
  const qs = year ? `?year=${year}` : '';
  const response = await fetch(`${API_BASE_URL}/reports/yearly${qs}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
};

export const getConflicts = async () => {
  const response = await fetch(`${API_BASE_URL}/conflicts`, { headers: getAuthHeaders() });
  return handleResponse(response);
};

export const getConflictById = async (transactionId) => {
  const response = await fetch(`${API_BASE_URL}/conflicts/${transactionId}`, { headers: getAuthHeaders() });
  return handleResponse(response);
};

export const resolveConflictItem = async (transactionId, resolution, note) => {
  const response = await fetch(`${API_BASE_URL}/conflicts/${transactionId}/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify({ resolution, note }),
  });
  return handleResponse(response);
};