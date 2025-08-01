import { useState, useEffect } from "react";
import "./TaskPage.css";
import api from "../utils/api";

export default function TaskPage({ tasks = [], onToggleTask, onDeleteTask, onAddTask, isLoading = false, onTaskUpdate }) {
  const [newTaskDescription, setNewTaskDescription] = useState("");
  const [newTaskEstimate, setNewTaskEstimate] = useState("");
  const [newTaskDueDate, setNewTaskDueDate] = useState("");
  const [newTaskDaysPerWeek, setNewTaskDaysPerWeek] = useState("");
  const [newTaskHoursPerDay, setNewTaskHoursPerDay] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [filter, setFilter] = useState('all');
  const [showBreakdownTaskId, setShowBreakdownTaskId] = useState(null);
  const [breakdownResult, setBreakdownResult] = useState('');
  const [isLoadingBreakdown, setIsLoadingBreakdown] = useState(false);

  // Function to format minutes as hours:minutes - UPDATED VERSION 2025
  const formatTimeEstimate = (minutes) => {
    if (!minutes || minutes === 0) return "";
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours === 0) {
      return `${mins}min`;
    } else if (mins === 0) {
      return `${hours}h`;
    } else {
      return `${hours}h ${mins}min`;
    }
  };

  const fetchTasks = () => {
    // Function stub for fetchTasks, may be used later
    console.log("Fetching tasks...");
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const formatDate = (dateString) => {
    if (!dateString) return "No due date";
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (newTaskDescription.trim()) {
      setIsSubmitting(true);

      const taskData = {
        description: newTaskDescription.trim(),
        completed: false
      };

      // Only include days_per_week and hours_per_day if they have values
      if (newTaskDaysPerWeek && !isNaN(newTaskDaysPerWeek)) {
        taskData.days_per_week = parseInt(newTaskDaysPerWeek);
      }
      
      if (newTaskHoursPerDay && !isNaN(newTaskHoursPerDay)) {
        taskData.hours_per_day = parseFloat(newTaskHoursPerDay);
      }

      if (newTaskEstimate) {
        taskData.estimated_minutes = parseInt(newTaskEstimate);
      }

      if (newTaskDueDate) {
        taskData.due_date = new Date(newTaskDueDate).toISOString();
      }

      const addTaskPromise = onAddTask(taskData);
      if (addTaskPromise && typeof addTaskPromise.then === 'function') {
        addTaskPromise.then(() => {
          setIsSubmitting(false);
          setNewTaskDescription("");
          setNewTaskEstimate("");
          setNewTaskDueDate("");
          setNewTaskDaysPerWeek("");
          setNewTaskHoursPerDay("");
        });
      } else {
        setIsSubmitting(false);
        setNewTaskDescription("");
        setNewTaskEstimate("");
        setNewTaskDueDate("");
        setNewTaskDaysPerWeek("");
        setNewTaskHoursPerDay("");
      }
    }
  };

  const filteredTasks = tasks.filter(task => {
    if (filter === 'all') return true;
    if (filter === 'pending') return !task.completed;
    if (filter === 'completed') return task.completed;
    return true;
  });

  const pendingTasksCount = tasks.filter(task => !task.completed).length;
  const completedTasksCount = tasks.filter(task => task.completed).length;

  return (
    <div className="page-container taskpage-container">
      <div className="task-page-content">
        <h1 className="page-title">Your Tasks</h1>
        <p className="page-subtitle">Manage your tasks efficiently and stay organized.</p>

        <div className="task-form-container">
        <h2>Add a New Task</h2>
        
        <div className="instructions">
          <p><strong>How to add tasks:</strong></p>
          <ul>
            <li><strong>Task description:</strong> Enter what you want to accomplish (e.g., "learn Python basics")</li>
            <li><strong>Due date:</strong> When you want to complete the task (optional)</li>
            <li><strong>Time fields:</strong> Leave blank for AI to estimate automatically, or fill in for custom scheduling</li>
            <li>Our AI will provide realistic time estimates and step-by-step breakdowns for beginners!</li>
          </ul>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="task-input-group">
            <input
              type="text"
              className="form-input"
              placeholder="Enter task description"
              value={newTaskDescription}
              onChange={(e) => setNewTaskDescription(e.target.value)}
              required
            />
            <input
              type="date"
              className="form-input"
              value={newTaskDueDate}
              onChange={(e) => setNewTaskDueDate(e.target.value)}
            />
          </div>
          <div className="task-input-group">
            <input
              type="number"
              className="form-input"
              placeholder="Estimated minutes (optional)"
              value={newTaskEstimate}
              onChange={(e) => setNewTaskEstimate(e.target.value)}
            />
            <input
              type="number"
              className="form-input"
              placeholder="Days per week (optional)"
              value={newTaskDaysPerWeek}
              onChange={(e) => setNewTaskDaysPerWeek(e.target.value)}
            />
            <input
              type="number"
              className="form-input"
              placeholder="Hours per day (optional)"
              value={newTaskHoursPerDay}
              onChange={(e) => setNewTaskHoursPerDay(e.target.value)}
            />
          </div>
          <div className="d-flex justify-content-center align-items-center">
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Adding...' : 'Add Task'}
            </button>
          </div>
        </form>
      </div>

      <div className="progress-section">
        <h2 className="mb-1">Overall Progress</h2>
        <progress value={tasks.length > 0 ? completedTasksCount : 0} max={tasks.length > 0 ? tasks.length : 1}></progress>
        <p>{completedTasksCount} of {tasks.length} tasks completed</p>
      </div>

      <div className="category-tabs">
        <button
          className={`category-tab all ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All ({tasks.length})
        </button>
        <button
          className={`category-tab pending ${filter === 'pending' ? 'active' : ''}`}
          onClick={() => setFilter('pending')}
        >
          Pending ({pendingTasksCount})
        </button>
        <button
          className={`category-tab completed ${filter === 'completed' ? 'active' : ''}`}
          onClick={() => setFilter('completed')}
        >
          Completed ({completedTasksCount})
        </button>
      </div>

      <div className="task-list-container">
        <h2 className="task-list-header">
          {filter === 'all' ? 'All Tasks' : filter === 'pending' ? 'Pending Tasks' : 'Completed Tasks'}
        </h2>
        {isLoading ? (
          <p>Loading tasks...</p>
        ) : filteredTasks.length === 0 ? (
          <p>No tasks in this category.</p>
        ) : (          <ul className="task-list">
            {filteredTasks.map(task => (
              <li key={task.id} className={`task-item ${task.completed ? 'completed' : ''}`}>
                <div className="task-item-content">
                  <strong className={task.completed ? 'text-muted' : ''}>{task.description}</strong>
                  <div className="task-item-details">
                    {task.due_date && <small className="text-muted">Due: {formatDate(task.due_date)}</small>}
                    {task.estimated_minutes && <small className="text-muted">Est: {formatTimeEstimate(task.estimated_minutes)}</small>}
                  </div>
                </div>
                <div className="task-actions">
                  {!task.completed && (
                    <button onClick={() => onToggleTask(task.id)} className="btn btn-success">Complete</button>
                  )}
                  <button onClick={() => onDeleteTask(task.id)} className="btn btn-danger">Delete</button>
                  <button 
                    onClick={() => {
                      if (showBreakdownTaskId === task.id) {
                        setShowBreakdownTaskId(null);
                      } else {
                        setShowBreakdownTaskId(task.id);
                        setIsLoadingBreakdown(true);
                        
                        // Show the breakdown from the task data if available
                        if (task.breakdown && task.breakdown.length > 0) {
                          const breakdownHtml = `<p>Task breakdown for "${task.description}":</p>
                            <ul>
                              ${task.breakdown.map(item => 
                                `<li><strong>${item.step}:</strong> ${item.summary} (${item.percentage}% of time)</li>`
                              ).join('')}
                            </ul>`;
                          setBreakdownResult(breakdownHtml);
                          setIsLoadingBreakdown(false);
                        } else {
                          // Fallback if no breakdown data available
                          const fallbackHtml = `<p>Task breakdown for "${task.description}":</p>
                            <ul>
                              <li><strong>Step 1: Planning and Research</strong> (25% of time)</li>
                              <li><strong>Step 2: Main Implementation</strong> (60% of time)</li>
                              <li><strong>Step 3: Review and Finalization</strong> (15% of time)</li>
                            </ul>`;
                          setBreakdownResult(fallbackHtml);
                          setIsLoadingBreakdown(false);
                        }
                      }
                    }} 
                    className="btn btn-info"
                    disabled={isLoadingBreakdown && showBreakdownTaskId === task.id}
                  >
                    {isLoadingBreakdown && showBreakdownTaskId === task.id ? 'Working...' : (showBreakdownTaskId === task.id ? 'Hide Breakdown' : 'Breakdown Task')}
                  </button>
                </div>
                {showBreakdownTaskId === task.id && (
                  <div className="task-breakdown-view">
                    {isLoadingBreakdown ? (
                      <p>Generating breakdown...</p>
                    ) : (
                      <>
                        <h4>Task Breakdown:</h4>
                        {breakdownResult ? (
                          <div className="breakdown-content" dangerouslySetInnerHTML={{ __html: breakdownResult }}></div>
                        ) : (
                          <p>No breakdown available or an error occurred.</p>
                        )}
                      </>
                    )}
                  </div>
                )}
              </li>
            ))}          </ul>
        )}
      </div>
      </div>
    </div>
  );
}
