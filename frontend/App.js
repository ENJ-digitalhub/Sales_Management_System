
import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ProductsPage from './pages/ProductsPage';
import SalesPage from './pages/SalesPage';
import PrivateRoute from './components/PrivateRoute';
import AuthProvider from './context/AuthContext';
import SyncInitializer from './components/SyncInitializer';

function App() {
  return (
    <Router>
      <AuthProvider>
        <SyncInitializer />
        <div className="App">
          <nav className="navbar">
            <ul className="nav-list">
              <li className="nav-item">
                <Link to="/login">Login</Link>
              </li>
              <li className="nav-item">
                <Link to="/dashboard">Dashboard</Link>
              </li>
              <li className="nav-item">
                <Link to="/products">Products</Link>
              </li>
              <li className="nav-item">
                <Link to="/sales">Sales</Link>
              </li>
            </ul>
          </nav>

          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/dashboard" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
            <Route path="/products" element={<PrivateRoute><ProductsPage /></PrivateRoute>} />
            <Route path="/sales" element={<PrivateRoute><SalesPage /></PrivateRoute>} />
            <Route path="/" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
          </Routes>
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;
