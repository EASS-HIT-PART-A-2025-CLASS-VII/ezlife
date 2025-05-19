// LoginPage.jsx - Login Page
import React, { useState } from "react";
import axios from "axios";
import "./LoginPage.css"; // Make sure this file is in the same folder

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const handleSubmit = async (e) => {
    e.preventDefault();
    // Use onLogin prop instead of direct axios call
    try {
      onLogin({ email, password });
    } catch (err) {
      setError("Invalid email or password. Please try again.");
    }
  };
  return (
    <div className="login-container">
      <header className="login-header">
        <h1>Sign In</h1>
        <p>Access your EZlife account.</p>
      </header>
      
      <div className="login-card">
        <form className="login-form" onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}          <div className="form-field">
            <label>Email address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-field">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>          <button type="submit" className="btn-primary">Sign In</button>
        </form>
      </div>
    </div>
  );
}
