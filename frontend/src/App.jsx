// App.jsx - Main Application
import React, { useState, useEffect } from 'react';
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
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentTheme, setCurrentTheme] = useState(localStorage.getItem('theme') || 'light');
  
  // Apply theme when app loads
  useEffect(() => {
    document.body.className = currentTheme;
  }, [currentTheme]);
  
  // Fetch tasks when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchTasks();
    }
  }, [isAuthenticated]);
  
  // Fetch all tasks from API
  const fetchTasks = () => {
    setLoading(true);
    api.get('/tasks')
      .then(response => {
        setTasks(response.data);
      })
      .catch(error => {
        console.error("Error fetching tasks:", error);
        // If there's an auth error, clear the token and redirect to login
        if (error.response && error.response.status === 401) {
          localStorage.removeItem('authToken');
          window.location.href = '/login';
        }
      })
      .finally(() => {
        setLoading(false);
      });
  };
  
  // Toggle task completion status
  const handleToggleTask = (taskId) => {
    api.patch(`/tasks/${taskId}`)
      .then(() => {
        // Update local state
        setTasks(tasks.map(task => 
          task.id === taskId ? { ...task, completed: !task.completed } : task
        ));
      })
      .catch(error => console.error("Error toggling task:", error));
  };
  
  // Delete a task
  const handleDeleteTask = (taskId) => {
    api.delete(`/tasks/${taskId}`)
      .then(() => {
        // Remove from local state
        setTasks(tasks.filter(task => task.id !== taskId));
      })
      .catch(error => console.error("Error deleting task:", error));
  };
  
  // Add a new task
  const handleAddTask = (taskData) => {
    // Return the promise so the TaskPage can know when the operation completes
    return api.post('/tasks', taskData)
      .then((response) => {
        console.log("Task added successfully with AI estimate:", response.data);
        // Add new task to local state
        setTasks([...tasks, response.data]);
        return response.data; // Return the data for potential further handling
      })
      .catch(error => {
        console.error("Error adding task:", error);
        throw error; // Re-throw so the caller can catch it if needed
      });
  };

  function handleLogin({ email, password }) {
    console.log("Attempting login with:", { email });
    
    // OAuth2 expects username/password in x-www-form-urlencoded format 
    const formData = new URLSearchParams();
    formData.append('username', email);  // OAuth2 uses 'username' field even for emails
    formData.append('password', password);
    formData.append('grant_type', 'password');  // This is standard for OAuth2
    
    // Log the request data
    console.log("Sending login request with OAuth2 form data to user-service");
    
    api.post('/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
      .then((response) => {
        console.log("Login successful:", response.data);
        if (!response.data.access_token) {
          console.error("No access token received!");
          alert("Login succeeded but no access token was received.");
          return;
        }
        localStorage.setItem('authToken', response.data.access_token);
        console.log("Token saved, now fetching tasks...");
        // Fetch tasks immediately after login
        fetchTasks(); 
        window.location.href = '/tasks';
      })
      .catch((error) => {
        console.error("Login error:", error);
        console.error("Error config:", error.config);
        console.error("Error response:", error.response?.data);
        if (error.request && !error.response) {
          alert("Network error: Could not connect to the authentication service. Please check if the server is running.");
        } else {
          alert(error.response?.data?.detail || 'Invalid credentials');
        }
      });
  }

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    window.location.href = '/';
  };
  
  // Handle theme switching from any component
  const handleThemeChange = (theme) => {
    localStorage.setItem('theme', theme);
    setCurrentTheme(theme);
    document.body.className = theme; // Immediately apply theme
  };

  return (
    <div className="App">
      <Router>
        <Navbar 
          isAuthenticated={isAuthenticated} 
          onLogout={handleLogout}
        />
        <div className="content">
          <Routes>
            <Route path="/" element={
              <HomePage 
                isAuthenticated={isAuthenticated} 
                onLogout={handleLogout}
                tasks={tasks} 
              />
            } />
            <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/settings" element={isAuthenticated ? <SettingsPage onThemeChange={handleThemeChange} /> : <Navigate to="/" />} />
            <Route path="/tasks" element={
              isAuthenticated ? 
                <TaskPage 
                  tasks={tasks}
                  onToggleTask={handleToggleTask}
                  onDeleteTask={handleDeleteTask}
                  onAddTask={handleAddTask}
                  isLoading={loading}
                /> : 
                <Navigate to="/login" />
            } />
            <Route path="*" element={<div>404 - Page Not Found</div>} /> {/* Fallback route */}
          </Routes>
        </div>
        <Footer /> {/* Add Footer component */}
      </Router>
    </div>
  );
}

export default App;
