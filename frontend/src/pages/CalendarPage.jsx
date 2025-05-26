import React, { useState, useEffect } from 'react';
import './CalendarPage.css'; // Import page-specific styles

function CalendarPage() {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [dailyActivities, setDailyActivities] = useState([]);
  const [newActivity, setNewActivity] = useState({ name: '', time: '' });
  const today = new Date();

  const [tasks, setTasks] = useState([
    { id: 1, title: 'Team Meeting', date: '2025-05-25', time: '10:00' },
    { id: 2, title: 'Project Deadline', date: '2025-05-28' },
    { id: 3, title: 'Client Call', date: '2025-06-02', time: '14:30' },
  ]);

  const handleAddActivity = () => {
    if (newActivity.name && newActivity.time) {
      setDailyActivities([...dailyActivities, { ...newActivity, id: Date.now() }]);
      setNewActivity({ name: '', time: '' });
    }
  };

  const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const isPreviousMonth = () => {
    return (
      currentMonth.getFullYear() < today.getFullYear() ||
      (currentMonth.getFullYear() === today.getFullYear() && 
       currentMonth.getMonth() < today.getMonth())
    );
  };

  const isNextMonth = () => {
    return (
      currentMonth.getFullYear() > today.getFullYear() ||
      (currentMonth.getFullYear() === today.getFullYear() && 
       currentMonth.getMonth() > today.getMonth())
    );
  };
  const renderCalendarGrid = () => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const firstDayOfMonth = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    let days = [];
    for (let i = 0; i < firstDayOfMonth; i++) {
      days.push(<div key={`empty-${i}`} className="calendar-day empty"></div>);
    }
    for (let day = 1; day <= daysInMonth; day++) {
      const currentDate = new Date(year, month, day);
      const currentDateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const dayTasks = tasks.filter(task => task.date === currentDateStr);

      const isToday = 
        currentDate.getDate() === today.getDate() &&
        currentDate.getMonth() === today.getMonth() &&
        currentDate.getFullYear() === today.getFullYear();

      days.push(
        <div key={day} className={`calendar-day ${isToday ? 'today' : ''}`}>
          <span className="day-number">{day}</span>
          {isToday && <span className="today-marker">Today</span>}
          <div className="tasks-on-day">
            {dayTasks.map(task => (
              <div key={task.id} className="calendar-task-item" title={task.title}>
                {task.time ? `${task.time} - ${task.title}` : task.title}
              </div>
            ))}
          </div>
        </div>
      );
    }
    return days;
  };  return (
    <div className="page-container calendarpage-container">
      <h1 className="page-title">Calendar & Schedule</h1>
      <p className="page-subtitle">View your tasks on the calendar and manage your daily recurring activities.</p>
      
      <div className="calendar-page-content">
        <div className="calendar-view">          <div className="calendar-header">
            <h2 className="month-year-title">
              {currentMonth.toLocaleString('default', { month: 'long' })}
              <span className="year-display">{currentMonth.getFullYear()}</span>
            </h2>
            <div className="calendar-nav-buttons">
              <button 
                onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1))} 
                className="btn-outline">
                &larr; Previous
              </button>
              <button 
                onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1))} 
                className="btn-outline">
                Next &rarr;
              </button>
            </div>
          </div>

          <div className="calendar-days-header">
            {daysOfWeek.map(day => (
              <div key={day} className="day-of-week">{day}</div>
            ))}
          </div>
          
          <div className="calendar-grid">
            {renderCalendarGrid()}
          </div>
        </div>
        
        <div className="schedule-section">
          <h2>Manage Daily Activities</h2>
          <p className="text-center subtitle mb-3">Add your typical work hours, breaks, classes, appointments, etc.</p>
          
          <div className="add-activity-form">
            <input 
              type="text" 
              placeholder="Activity Name (e.g., Work Block)" 
              className="input-field" 
              value={newActivity.name}
              onChange={(e) => setNewActivity({...newActivity, name: e.target.value})}
            />
            <input 
              type="time" 
              className="input-field" 
              value={newActivity.time}
              onChange={(e) => setNewActivity({...newActivity, time: e.target.value})}
            />
            <button 
              onClick={handleAddActivity} 
              className="btn btn-primary"
              disabled={!newActivity.name || !newActivity.time}
            >
              Add Activity
            </button>
          </div>
          
          <div className="activities-list">
            {dailyActivities.length > 0 ? (
              dailyActivities.map(activity => (
                <div key={activity.id} className="activity-item">
                  <span><strong>{activity.time}</strong> - {activity.name}</span>
                  <button 
                    className="btn btn-danger btn-small" 
                    onClick={() => setDailyActivities(dailyActivities.filter(a => a.id !== activity.id))}
                  >
                    Remove
                  </button>
                </div>
              ))
            ) : (
              <div className="no-activities">
                <p className="text-center">No daily activities scheduled yet.</p>
                <p className="text-center text-muted">Add activities to organize your day</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default CalendarPage;
