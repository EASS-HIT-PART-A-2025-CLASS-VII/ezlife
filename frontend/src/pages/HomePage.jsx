// HomePage.jsx - Home Page
import React from 'react';
import { Link } from 'react-router-dom';
import "./HomePage.css";

// Task Progress component
const TaskProgress = ({ tasks = [] }) => {
  // Calculate task statistics
  const completedTasks = tasks.filter(task => task.completed).length;
  const totalTasks = tasks.length;
  const completionRate = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;
  
  // Calculate overdue tasks (due date is in the past and task is not completed)
  const overdueTasks = tasks.filter(task => 
    !task.completed && 
    task.due_date && 
    new Date(task.due_date) < new Date()
  ).length;
  
  const todayTasks = tasks.filter(task => {
    if (!task.due_date) return false;
    const dueDate = new Date(task.due_date);
    const today = new Date();
    return !task.completed &&
          dueDate.getDate() === today.getDate() &&
          dueDate.getMonth() === today.getMonth() &&
          dueDate.getFullYear() === today.getFullYear();
  }).length;
  
  return (
    <div className="task-progress">
      <h3>Task Progress</h3>
        <div className="progress-bar-container">
        <div 
          className={`progress-bar ${
            completionRate >= 75 ? 'high-progress' : 
            completionRate >= 50 ? 'medium-progress' : 
            completionRate >= 25 ? 'low-progress' : 'very-low-progress'
          }`}
          style={{ width: `${completionRate}%` }}
          aria-valuenow={completionRate}
          aria-valuemin="0"
          aria-valuemax="100"
        >
          {completionRate.toFixed(0)}%
        </div>
      </div>
      
      <div className="task-stats">
        <div className="stat-item">
          <span className="stat-value">{completedTasks}</span>
          <span className="stat-label">Completed</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{totalTasks - completedTasks}</span>
          <span className="stat-label">Remaining</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{todayTasks}</span>
          <span className="stat-label">Today</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{overdueTasks}</span>
          <span className="stat-label">Overdue</span>
        </div>
      </div>
    </div>
  );
};

export default function HomePage({ isAuthenticated, onLogout, tasks = [] }) {
  return (
    <div className="page-container"> {/* Use common page-container */}
      <div className="homepage-content-wrapper"> {/* Wrapper for homepage specific layout */}
        <header className="homepage-header">
          <h1>Welcome to EZlife</h1>
          <p>Organize your tasks effortlessly with our modern task manager.</p>
        </header>
        
        {isAuthenticated ? (
          <div className="logged-in-container">
            <div className="welcome-message">
              <h2>Your Dashboard</h2>
              <p>Good to see you again! Ready to be productive today?</p>
              <button onClick={onLogout} className="btn-logout">Logout</button>
            </div>
            
            {/* Task Progress Component */}
            <TaskProgress tasks={tasks} />
            
            <div className="feature-cards">
              <div className="feature-card">
                <div className="feature-icon">📝</div>
                <h3>Manage Tasks</h3>
                <p>Create, track, and complete your daily tasks.</p>
                <Link to="/tasks" className="btn-primary">Go to Tasks</Link>
              </div>
              
              <div className="feature-card">
                <div className="feature-icon">⏱️</div>
                <h3>Time Estimation</h3>
                <p>AI-powered time estimation helps you plan your day better.</p>
              </div>
              
              <div className="feature-card">
                <div className="feature-icon">📅</div>
                <h3>Due Date Tracking</h3>
                <p>Never miss a deadline with our due date reminders.</p>
              </div>
            </div>
            
            <div className="quick-stats">
              <h3>Quick Tips</h3>
              <ul>
                <li>Break down large tasks into smaller ones</li>
                <li>Use AI time estimation for better planning</li>
                <li>Set realistic due dates for your tasks</li>
              </ul>
            </div>
          </div>        ) : (
          <div className="not-logged-in-container">
            <div className="welcome-banner">
              <h2>Get Started with EZlife</h2>
              <p>The easiest way to organize your life and boost productivity.</p>
              <div className="feature-highlights">
                <div className="feature-highlight">
                  <div className="feature-icon">📝</div>
                  <h3>Task Management</h3>
                  <p>Create, organize, and complete tasks with ease.</p>
                </div>
                <div className="feature-highlight">
                  <div className="feature-icon">⏱️</div>
                  <h3>Smart Time Estimation</h3>
                  <p>AI-powered time estimation for better planning.</p>
                </div>
                <div className="feature-highlight">
                  <div className="feature-icon">📁</div>
                  <h3>File Storage</h3>
                  <p>Keep all your important files in one place.</p>
                </div>
              </div>
            </div>
            <div className="homepage-actions">
              <Link to="/login" className="btn-primary">Login</Link>
              <Link to="/register" className="btn-secondary">Create Account</Link>
            </div>
          </div>
        )}
      </div> {/* Close homepage-content-wrapper */}
    </div>
  );
}
