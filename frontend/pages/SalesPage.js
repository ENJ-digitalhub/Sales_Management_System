
import React, { useState, useEffect } from 'react';
import { createSale, getSales, getSale, editSale, cancelSale, getProducts } from '../services/api';
import { getAllItems, addItem, putItem, deleteItem as deleteLocalItem } from '../services/local_db';
import { useAuth } from '../context/AuthContext';

const SalesPage = () => {
  const [sales, setSales] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newSale, setNewSale] = useState({
    items: [], payment_method: 'cash'
  });
  const [editingSale, setEditingSale] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    fetchSalesAndProducts();
  }, []);

  const fetchSalesAndProducts = async () => {
    try {
      setLoading(true);
      // Try to fetch from API first
      const salesResponse = await getSales();
      if (salesResponse.success) {
        setSales(salesResponse.sales);
        // Store in IndexedDB
        for (const sale of salesResponse.sales) {
          await putItem('sales', sale);
        }
      } else {
        setError(salesResponse.message);
        // Fallback to IndexedDB if API fails
        const localSales = await getAllItems('sales');
        setSales(localSales);
      }

      const productsResponse = await getProducts();
      if (productsResponse.success) {
        setProducts(productsResponse.products.filter(p => p.is_active));
        for (const product of productsResponse.products) {
          await putItem('products', product);
        }
      } else {
        setError(productsResponse.message);
        const localProducts = await getAllItems('products');
        setProducts(localProducts);
      }
    } catch (err) {
      console.error('Failed to fetch sales/products from API, trying local DB:', err);
      setError(err.message);
      try {
        const localSales = await getAllItems('sales');
        setSales(localSales);
        const localProducts = await getAllItems('products');
        setProducts(localProducts);
      } catch (localErr) {
        setError('Failed to load sales/products from local database: ' + localErr.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleNewSaleChange = (e) => {
    const { name, value } = e.target;
    setNewSale(prev => ({ ...prev, [name]: value }));
  };

  const handleAddItemToSale = (productId, quantity) => {
    const product = products.find(p => p.id === productId);
    if (!product) {
      setError('Product not found');
      return;
    }
    if (quantity <= 0) {
      setError('Quantity must be positive');
      return;
    }
    if (product.stock_quantity < quantity) {
      setError(`Insufficient stock for ${product.name}. Available: ${product.stock_quantity}`);
      return;
    }

    setNewSale(prev => {
      const existingItemIndex = prev.items.findIndex(item => item.product_id === productId);
      if (existingItemIndex > -1) {
        const updatedItems = [...prev.items];
        updatedItems[existingItemIndex].quantity += quantity;
        return { ...prev, items: updatedItems };
      } else {
        return { ...prev, items: [...prev.items, { product_id: productId, quantity }] };
      }
    });
  };

  const handleCreateSale = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const response = await createSale(newSale);
      if (response.success) {
        setNewSale({ items: [], payment_method: 'cash' });
        fetchSalesAndProducts(); // Refresh data
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCancelSale = async (saleId) => {
    if (window.confirm('Are you sure you want to cancel this sale?')) {
      setError('');
      try {
        const response = await cancelSale(saleId);
        if (response.success) {
          fetchSalesAndProducts(); // Refresh data
        } else {
          setError(response.message);
        }
      } catch (err) {
        setError(err.message);
      }
    }
  };

  if (loading) return <div>Loading sales data...</div>;
  if (error) return <div className="error-message">Error: {error}</div>;

  const canManageSales = user && (user.role === 'admin' || user.role === 'manager' || user.role === 'employee');

  return (
    <div className="sales-container">
      <h2>Sales Management</h2>

      {canManageSales && (
        <div className="sale-form">
          <h3>Create New Sale</h3>
          <form onSubmit={handleCreateSale}>
            <div>
              <h4>Add Items</h4>
              {products.map(product => (
                <div key={product.id}>
                  <span>{product.name} (${product.selling_price.toFixed(2)}) - Stock: {product.stock_quantity}</span>
                  <input
                    type="number"
                    min="1"
                    max={product.stock_quantity}
                    defaultValue="1"
                    onChange={(e) => {
                      const qty = parseInt(e.target.value);
                      if (qty > 0 && qty <= product.stock_quantity) {
                        handleAddItemToSale(product.id, qty);
                      }
                    }}
                  />
                </div>
              ))}
            </div>
            <div>
              <h4>Selected Items:</h4>
              {newSale.items.length === 0 ? (
                <p>No items added yet.</p>
              ) : (
                <ul>
                  {newSale.items.map(item => {
                    const product = products.find(p => p.id === item.product_id);
                    return (
                      <li key={item.product_id}>
                        {product ? product.name : 'Unknown Product'} - Quantity: {item.quantity}
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
            <label htmlFor="payment_method">Payment Method:</label>
            <select name="payment_method" id="payment_method" value={newSale.payment_method} onChange={handleNewSaleChange}>
              <option value="cash">Cash</option>
              <option value="transfer">Transfer</option>
              <option value="pos">POS</option>
            </select>
            <button type="submit">Create Sale</button>
          </form>
        </div>
      )}

      <h3>Recent Sales</h3>
      <div className="sales-list">
        {sales.length === 0 ? (
          <p>No sales recorded yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Receipt #</th>
                <th>Total Amount</th>
                <th>Payment Method</th>
                <th>Status</th>
                <th>Created At</th>
                {canManageSales && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {sales.map(sale => (
                <tr key={sale.id}>
                  <td>{sale.receipt_number}</td>
                  <td>${sale.total_amount.toFixed(2)}</td>
                  <td>{sale.payment_method}</td>
                  <td>{sale.status}</td>
                  <td>{new Date(sale.created_at).toLocaleString()}</td>
                  {canManageSales && (
                    <td>
                      <button onClick={() => handleCancelSale(sale.id)} disabled={sale.status === 'cancelled' || (user.role === 'employee' && new Date() > new Date(sale.editable_until))}>Cancel</button>
                      {/* Add Edit functionality later */}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default SalesPage;
