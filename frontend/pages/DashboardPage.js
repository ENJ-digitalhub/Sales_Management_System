
import React from 'react';
import { useAuth } from '../context/AuthContext';

const DashboardPage = () => {
  const { user } = useAuth();

  return (
    <div className="dashboard-container">
      <h2>Welcome, {user ? user.name : 'Guest'}!</h2>
      <p>Role: {user ? user.role : 'N/A'}</p>
      <h3>Dashboard Overview</h3>
      <p>This is where you'll see key metrics and quick actions.</p>
      {/* Add more dashboard content here */}
    </div>
  );
};

export default DashboardPage;
