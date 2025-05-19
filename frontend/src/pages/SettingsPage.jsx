// SettingsPage.jsx - User Settings Page
import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import './SettingsPage.css';

function SettingsPage({ onThemeChange }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [message, setMessage] = useState('');
  const [notificationsEnabled, setNotificationsEnabled] = useState(
    localStorage.getItem('notificationsEnabled') === 'true'
  );

  useEffect(() => {
    // Apply theme when component mounts or theme changes
    document.body.className = theme;
    localStorage.setItem('theme', theme);
  }, [theme]);

  const handleSave = async () => {
    try {
      // Only send data that was actually changed
      const updateData = {};
      if (email) updateData.email = email;
      if (password) updateData.password = password;
      
      await api.post('/settings', updateData);
      setMessage('Settings updated successfully!');
      
      // Save preferences to localStorage
      localStorage.setItem('notificationsEnabled', notificationsEnabled);
      
      // Clear form after successful update
      if (email) setEmail('');
      if (password) setPassword('');
    } catch (error) {
      console.error('Error updating settings:', error);
      setMessage('Update failed. Please try again.');
    }
  };
  const handleThemeChange = (newTheme) => {
    setTheme(newTheme);
    // Call the parent component's theme handler if available
    if (onThemeChange) {
      onThemeChange(newTheme);
    }
  };

  const handleNotificationToggle = () => {
    setNotificationsEnabled(!notificationsEnabled);
  };

  return (
    <div className="settings-container">
      <header className="settings-header">
        <h1>Account Settings</h1>
        <p>Update your account information and preferences.</p>
      </header>
      
      <div className="settings-content">
        <div className="settings-card">
          <h2>Profile Information</h2>
          {message && <p className={message.includes('failed') ? 'error-message' : 'success-message'}>{message}</p>}
          
          <div className="settings-form">
            <div className="form-group">
              <label>Email</label>
              <input 
                type="email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                placeholder="Enter new email address" 
              />
            </div>
            
            <div className="form-group">
              <label>Password</label>
              <input 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                placeholder="Enter new password" 
              />
            </div>
          </div>
        </div>
        
        <div className="settings-card">
          <h2>Theme Preferences</h2>
          <p>Choose your preferred theme for EZlife.</p>
          
          <div className="theme-options">
            <div 
              className={`theme-option ${theme === 'light' ? 'selected' : ''}`}
              onClick={() => handleThemeChange('light')}
            >
              <div className="theme-preview light-theme"></div>
              <span>Light</span>
            </div>
            
            <div 
              className={`theme-option ${theme === 'dark' ? 'selected' : ''}`}
              onClick={() => handleThemeChange('dark')}
            >
              <div className="theme-preview dark-theme"></div>
              <span>Dark</span>
            </div>
            
            <div 
              className={`theme-option ${theme === 'colorful' ? 'selected' : ''}`}
              onClick={() => handleThemeChange('colorful')}
            >
              <div className="theme-preview colorful-theme"></div>
              <span>Colorful</span>
            </div>
          </div>
        </div>
        
        <div className="settings-card">
          <h2>Notifications</h2>
          <div className="notification-settings">
            <div className="toggle-option">
              <span>Task Due Date Reminders</span>
              <label className="toggle-switch">
                <input 
                  type="checkbox" 
                  checked={notificationsEnabled}
                  onChange={handleNotificationToggle}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>
        
        <button className="save-button" onClick={handleSave}>
          Save Changes
        </button>
      </div>
    </div>
  );
}

export default SettingsPage;
