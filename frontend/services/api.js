
const API_BASE_URL = 'http://127.0.0.1:5000';

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

export const getProducts = async () => {
  const response = await fetch(`${API_BASE_URL}/products`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
};

export const createProduct = async (productData) => {
  const response = await fetch(`${API_BASE_URL}/products`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(productData),
  });
  return handleResponse(response);
};

export const updateProduct = async (productId, productData) => {
  const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
    body: JSON.stringify(productData),
  });
  return handleResponse(response);
};

export const deleteProduct = async (productId) => {
  const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
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
