import { useState } from "react";
import "./TaskPage.css";

// Add Font Awesome for icons
const iconStyle = {
  marginRight: '5px'
};

export default function TaskPage({ tasks = [], onToggleTask, onDeleteTask, onAddTask, isLoading = false }) {
  console.log("TaskPage rendered with tasks:", tasks);
  const [newTaskDescription, setNewTaskDescription] = useState("");
  const [newTaskEstimate, setNewTaskEstimate] = useState("");
  const [newTaskDueDate, setNewTaskDueDate] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeCategory, setActiveCategory] = useState("all");
  const [aiEstimating, setAiEstimating] = useState(false);  // New state for AI estimation status
  
  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return "No due date";
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (newTaskDescription.trim()) {
      setIsSubmitting(true);
      
      // If no time estimate is provided, indicate AI is estimating
      if (!newTaskEstimate) {
        setAiEstimating(true);
      }
      
      const taskData = { 
        description: newTaskDescription.trim(),
        completed: false
      };
      
      // Add estimate if provided
      if (newTaskEstimate) {
        taskData.estimated_minutes = parseInt(newTaskEstimate);
      }
      
      // Add due date if provided
      if (newTaskDueDate) {
        taskData.due_date = new Date(newTaskDueDate).toISOString();
      }
      
      // Call onAddTask and handle the promise completion
      const addTaskPromise = onAddTask(taskData);
      
      // If onAddTask returns a promise, wait for it to complete
      if (addTaskPromise && typeof addTaskPromise.then === 'function') {
        addTaskPromise.then(() => {
          setIsSubmitting(false);
          setAiEstimating(false);
          
          // Reset form
          setNewTaskDescription("");
          setNewTaskEstimate("");
          setNewTaskDueDate("");
        });
      } else {
        // If it's not a promise, just reset the state
        setIsSubmitting(false);
        setAiEstimating(false);
        
        // Reset form
        setNewTaskDescription("");
        setNewTaskEstimate("");
        setNewTaskDueDate("");
      }
    }
  };

  // Calculate task statistics
  const completedTasks = tasks.filter(task => task.completed).length;
  const totalTasks = tasks.length;
  const completionRate = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

  // Filter tasks based on active category
  const filterTasksByCategory = () => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    // Helper function to check if a date is today
    const isToday = (dateString) => {
      if (!dateString) return false;
      const date = new Date(dateString);
      return date >= today && date < tomorrow;
    };
    
    // Helper function to check if a date is in the future (not today)
    const isFuture = (dateString) => {
      if (!dateString) return false;
      const date = new Date(dateString);
      return date >= tomorrow;
    };
    
    // Helper function to check if a date is in the past
    const isPast = (dateString) => {
      if (!dateString) return false;
      const date = new Date(dateString);
      return date < today;
    };
    
    switch (activeCategory) {
      case 'today':
        return tasks.filter(task => !task.completed && isToday(task.due_date));
      case 'upcoming':
        return tasks.filter(task => !task.completed && isFuture(task.due_date));
      case 'overdue':
        return tasks.filter(task => !task.completed && isPast(task.due_date));
      case 'completed':
        return tasks.filter(task => task.completed);
      case 'all':
      default:
        return tasks;
    }
  };
  
  const filteredTasks = filterTasksByCategory();
  
  // Task category counts for displaying badges
  const categoryCounts = {
    all: tasks.length,
    today: tasks.filter(task => {
      if (!task.due_date || task.completed) return false;
      const dueDate = new Date(task.due_date);
      const today = new Date();
      return dueDate.getDate() === today.getDate() &&
             dueDate.getMonth() === today.getMonth() &&
             dueDate.getFullYear() === today.getFullYear();
    }).length,
    upcoming: tasks.filter(task => {
      if (!task.due_date || task.completed) return false;
      const dueDate = new Date(task.due_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      return dueDate >= tomorrow;
    }).length,
    overdue: tasks.filter(task => {
      if (!task.due_date || task.completed) return false;
      const dueDate = new Date(task.due_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      return dueDate < today;
    }).length,
    completed: completedTasks
  };
  
  return (
    <div className="taskpage-container">
      <header className="taskpage-header">
        <h1>Your Tasks</h1>
        <p>Manage your tasks efficiently and stay organized.</p>
      </header>
      
      <div className="task-content-container">
        <form onSubmit={handleSubmit} className="add-task-form">
          <div className="form-row">
            <input
              type="text"
              placeholder="Add a new task..."
              value={newTaskDescription}
              onChange={(e) => setNewTaskDescription(e.target.value)}
              className="task-input"
              disabled={isSubmitting}
              required
            />
          </div>          <div className="form-row">
            <div className="estimate-input-container">
              <input
                type="number"
                placeholder={aiEstimating ? "AI is estimating..." : "Estimated minutes (leave blank for AI estimate)"}
                value={newTaskEstimate}
                onChange={(e) => setNewTaskEstimate(e.target.value)}
                className={`task-estimate ${aiEstimating ? 'ai-estimating' : ''}`}
                disabled={isSubmitting}
                min="1"
              />
              {aiEstimating && <div className="ai-estimate-spinner"></div>}
            </div>
            <input
              type="date"
              placeholder="Due date"
              value={newTaskDueDate}
              onChange={(e) => setNewTaskDueDate(e.target.value)}
              className="task-due-date"
              disabled={isSubmitting}
            />
            <button type="submit" className="btn-add" disabled={isSubmitting || !newTaskDescription.trim()}>
              {isSubmitting ? (aiEstimating ? 'Estimating...' : 'Adding...') : 'Add Task'}
            </button>
          </div>
        </form>
        
        {/* Overall progress bar */}
        <div className="task-progress">
          <h3>Overall Progress</h3>
          <div className="progress-bar-container">
            <div 
              className="progress-bar" 
              style={{ width: `${completionRate}%` }}
              aria-valuenow={completionRate}
              aria-valuemin="0"
              aria-valuemax="100"
            >
              {completionRate.toFixed(0)}%
            </div>
          </div>
          <div className="progress-stats">
            <div className="progress-stat">
              <span>{completedTasks}</span> of <span>{totalTasks}</span> tasks completed
            </div>
          </div>
        </div>
        
        {/* Task category tabs */}
        <div className="task-categories">
          <button 
            className={`category-tab ${activeCategory === 'all' ? 'active' : ''}`}
            onClick={() => setActiveCategory('all')}
          >
            All <span className="category-count">{categoryCounts.all}</span>
          </button>
          <button 
            className={`category-tab ${activeCategory === 'today' ? 'active' : ''}`}
            onClick={() => setActiveCategory('today')}
          >
            Today <span className="category-count">{categoryCounts.today}</span>
          </button>
          <button 
            className={`category-tab ${activeCategory === 'upcoming' ? 'active' : ''}`}
            onClick={() => setActiveCategory('upcoming')}
          >
            Upcoming <span className="category-count">{categoryCounts.upcoming}</span>
          </button>
          <button 
            className={`category-tab ${activeCategory === 'overdue' ? 'active' : ''}`}
            onClick={() => setActiveCategory('overdue')}
          >
            Overdue <span className="category-count danger">{categoryCounts.overdue}</span>
          </button>
          <button 
            className={`category-tab ${activeCategory === 'completed' ? 'active' : ''}`}
            onClick={() => setActiveCategory('completed')}
          >
            Completed <span className="category-count success">{categoryCounts.completed}</span>
          </button>
        </div>
      
        <div className="tasks-section">
          <h2>{activeCategory.charAt(0).toUpperCase() + activeCategory.slice(1)} Tasks</h2>
          <ul className="task-list">
            {isLoading ? (
              <li className="loading-tasks">Loading tasks...</li>
            ) : filteredTasks.length > 0 ? (
              filteredTasks.map((task) => (
                <li key={task.id} className={`task-item ${task.completed ? "completed" : ""}`}>
                  <div className="task-content">
                    <h3 className="task-description">{task.description}</h3>
                    <div className="task-details">                  
                      {task.estimated_minutes > 0 && (
                        <span className="task-estimate">
                          <span style={iconStyle}>⏱️</span> Estimate: {task.estimated_minutes} minutes
                        </span>
                      )}
                      {task.due_date && (
                        <span className={`task-due-date ${new Date(task.due_date) < new Date() && !task.completed ? 'overdue' : ''}`}>
                          <span style={iconStyle}>📅</span> Due: {formatDate(task.due_date)}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="task-actions">
                    <button onClick={() => onToggleTask(task.id)} className={`btn-toggle ${task.completed ? 'completed' : ''}`}>
                      {task.completed ? "Undo" : "Complete"}
                    </button>
                    <button onClick={() => onDeleteTask(task.id)} className="btn-delete">Delete</button>
                  </div>
                </li>
              ))
            ) : (
              <li className="no-tasks">No {activeCategory} tasks found.</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
