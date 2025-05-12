// HomePage.jsx - Home Page
import React from 'react';
import "./HomePage.css";

export default function HomePage({ isAuthenticated }) {
  return (
    <div className="homepage-container">
      <header className="homepage-header">
        <h1>Welcome to EZlife</h1>
        <p>Organize your tasks effortlessly with our modern task manager.</p>
      </header>
      <div className="homepage-actions">
        {isAuthenticated && (
          <a href="/tasks" className="btn-primary">Start Managing Tasks</a>
        )}
        <a href="/login" className="btn-secondary">Login</a>
        <a href="/register" className="btn-secondary">Register</a>
      </div>
    </div>
  );
}
