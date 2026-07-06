
import React, { useState, useEffect } from 'react';
import { getProducts, createProduct, updateProduct, deleteProduct } from '../services/api';
import { getAllItems, addItem, putItem, deleteItem as deleteLocalItem } from '../services/local_db';
import { useAuth } from '../context/AuthContext';

const ProductsPage = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newProduct, setNewProduct] = useState({
    name: '', category: '', selling_price: '', cost_price: '', stock_quantity: ''
  });
  const [editingProduct, setEditingProduct] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      // Try to fetch from API first
      const apiResponse = await getProducts();
      if (apiResponse.success) {
        setProducts(apiResponse.products);
        // Store in IndexedDB
        for (const product of apiResponse.products) {
          await putItem('products', product);
        }
      } else {
        setError(apiResponse.message);
        // Fallback to IndexedDB if API fails
        const localProducts = await getAllItems('products');
        setProducts(localProducts);
      }
    } catch (err) {
      console.error('Failed to fetch products from API, trying local DB:', err);
      setError(err.message);
      // Fallback to IndexedDB if API call fails
      try {
        const localProducts = await getAllItems('products');
        setProducts(localProducts);
      } catch (localErr) {
        setError('Failed to load products from local database: ' + localErr.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleNewProductChange = (e) => {
    const { name, value } = e.target;
    setNewProduct(prev => ({ ...prev, [name]: value }));
  };

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const response = await createProduct(newProduct);
      if (response.success) {
        setNewProduct({ name: '', category: '', selling_price: '', cost_price: '', stock_quantity: '' });
        fetchProducts();
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEditClick = (product) => {
    setEditingProduct({ ...product, selling_price: String(product.selling_price), cost_price: String(product.cost_price) });
  };

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditingProduct(prev => ({ ...prev, [name]: value }));
  };

  const handleUpdateProduct = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const response = await updateProduct(editingProduct.id, editingProduct);
      if (response.success) {
        setEditingProduct(null);
        fetchProducts();
      } else {
        setError(response.message);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteProduct = async (productId) => {
    if (window.confirm('Are you sure you want to deactivate this product?')) {
      setError('');
      try {
        const response = await deleteProduct(productId);
        if (response.success) {
          fetchProducts();
        } else {
          setError(response.message);
        }
      } catch (err) {
        setError(err.message);
      }
    }
  };

  if (loading) return <div>Loading products...</div>;
  if (error) return <div className="error-message">Error: {error}</div>;

  const canManageProducts = user && (user.role === 'admin' || user.role === 'manager');

  return (
    <div className="products-container">
      <h2>Products Management</h2>

      {canManageProducts && (
        <div className="product-form">
          <h3>{editingProduct ? 'Edit Product' : 'Add New Product'}</h3>
          <form onSubmit={editingProduct ? handleUpdateProduct : handleCreateProduct}>
            <input type="text" name="name" placeholder="Product Name" value={editingProduct ? editingProduct.name : newProduct.name} onChange={editingProduct ? handleEditChange : handleNewProductChange} required />
            <input type="text" name="category" placeholder="Category" value={editingProduct ? editingProduct.category : newProduct.category} onChange={editingProduct ? handleEditChange : handleNewProductChange} />
            <input type="number" name="selling_price" placeholder="Selling Price" value={editingProduct ? editingProduct.selling_price : newProduct.selling_price} onChange={editingProduct ? handleEditChange : handleNewProductChange} step="0.01" required />
            <input type="number" name="cost_price" placeholder="Cost Price" value={editingProduct ? editingProduct.cost_price : newProduct.cost_price} onChange={editingProduct ? handleEditChange : handleNewProductChange} step="0.01" required />
            <input type="number" name="stock_quantity" placeholder="Stock Quantity" value={editingProduct ? editingProduct.stock_quantity : newProduct.stock_quantity} onChange={editingProduct ? handleEditChange : handleNewProductChange} required />
            <button type="submit">{editingProduct ? 'Update Product' : 'Add Product'}</button>
            {editingProduct && <button type="button" onClick={() => setEditingProduct(null)}>Cancel Edit</button>}
          </form>
        </div>
      )}

      <h3>Available Products</h3>
      <div className="product-list">
        {products.length === 0 ? (
          <p>No products found.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Category</th>
                <th>Selling Price</th>
                <th>Cost Price</th>
                <th>Stock</th>
                <th>Status</th>
                {canManageProducts && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {products.map(product => (
                <tr key={product.id}>
                  <td>{product.name}</td>
                  <td>{product.category || 'N/A'}</td>
                  <td>${product.selling_price.toFixed(2)}</td>
                  <td>${product.cost_price.toFixed(2)}</td>
                  <td>{product.stock_quantity}</td>
                  <td>{product.is_active ? 'Active' : 'Inactive'}</td>
                  {canManageProducts && (
                    <td>
                      <button onClick={() => handleEditClick(product)}>Edit</button>
                      <button onClick={() => handleDeleteProduct(product.id)} disabled={!product.is_active}>Deactivate</button>
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

export default ProductsPage;
