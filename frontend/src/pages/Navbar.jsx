// Navbar.jsx - Navigation Bar
import React from 'react';
import { Link } from 'react-router-dom';
import "./Navbar.css";

export default function Navbar({ isAuthenticated, onLogout }) {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">EZlife</Link>
      </div>      <div className="navbar-links">
        <Link to="/">Home</Link>
        {isAuthenticated ? (
          <>
            <Link to="/tasks">Tasks</Link>
            <Link to="/settings">Settings</Link>
            <button onClick={onLogout} className="btn-logout">Logout</button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
}
