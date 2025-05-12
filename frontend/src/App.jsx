// App.jsx - Main Application
import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import SettingsPage from './pages/SettingsPage';
import TaskPage from './pages/TaskPage';
import Navbar from './pages/Navbar'; // Ensure Navbar is imported correctly
import Footer from './pages/Footer'; // Import Footer component
import api from './utils/api';

function App() {
  const isAuthenticated = !!localStorage.getItem('authToken');

  function handleLogin({ email, password }) {
    api.post('/token', new URLSearchParams({
      username: email,
      password: password,
    }))
      .then((response) => {
        localStorage.setItem('authToken', response.data.access_token);
        window.location.href = '/tasks';
      })
      .catch((error) => {
        alert(error.response?.data?.detail || 'Invalid credentials');
      });
  }

  return (
    <div className="App">
      <Router>
        <Navbar 
          isAuthenticated={isAuthenticated} 
          onLogout={() => {
            localStorage.removeItem('authToken');
            window.location.href = '/';
          }} 
        />
        <div className="content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/settings" element={isAuthenticated ? <SettingsPage /> : <Navigate to="/" />} />
            <Route path="/tasks" element={isAuthenticated ? <TaskPage /> : <Navigate to="/login" />} />
            <Route path="*" element={<div>404 - Page Not Found</div>} /> {/* Fallback route */}
          </Routes>
        </div>
        <Footer /> {/* Add Footer component */}
      </Router>
    </div>
  );
}

export default App;
