import React, { useState, useEffect, useRef } from 'react';
import './CalendarPage.css'; // Import page-specific styles
import api from '../utils/api'; // Import API utility

function CalendarPage() {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [dailyActivities, setDailyActivities] = useState([]);
  const [newActivity, setNewActivity] = useState({ name: '', time: '', date: new Date().toISOString().split('T')[0] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);
  const [modalPosition, setModalPosition] = useState({ left: 0, top: 0 });
  const [showModal, setShowModal] = useState(false);
  const modalRef = useRef(null);
  const today = new Date();

  // This state is now unused and can be removed.
  // const [tasks, setTasks] = useState([
  //   { id: 1, title: 'Team Meeting', date: '2025-05-25', time: '10:00' },
  //   { id: 2, title: 'Project Deadline', date: '2025-05-28' },
  //   { id: 3, title: 'Client Call', date: '2025-06-02', time: '14:30' },
  // ]);

  // Effect to fetch activities when the component mounts
  useEffect(() => {
    fetchActivities();
  }, []);

  // Function to fetch activities from the backend
  const fetchActivities = async () => {
    try {
      setIsLoading(true);
      setError(null);
      console.log("Fetching activities from the backend...");
      
      const response = await api.get('/activities/');
      
      console.log("Activities received:", response.data);
      
      if (Array.isArray(response.data)) {
        setDailyActivities(response.data);
      } else {
        console.error("Invalid response format:", response.data);
        setError("Received an invalid format for activities.");
      }
      
    } catch (err) {
      console.error("Failed to fetch activities:", err);
      setError("Failed to load activities. Please check your connection and try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle adding a new activity
  const handleAddActivity = async () => {
    if (newActivity.name && newActivity.time && newActivity.date) {
      try {
        console.log("Adding activity:", newActivity);
        
        // Save to backend
        const response = await api.post('/activities/', newActivity);
        console.log("Activity saved, response:", response.data);
        
        // Add the new activity returned from the server to the state
        setDailyActivities(prevActivities => [...prevActivities, response.data]);
        
        // Reset the form but keep the currently selected date
        const currentDate = newActivity.date;
        setNewActivity({ name: '', time: '', date: currentDate });

      } catch (err) {
        console.error("Failed to save activity:", err);
        setError("Failed to save activity. Please try again.");
      }
    }
  };

  // Handle deleting an activity
  const handleDeleteActivity = async (activityId) => {
    try {
      console.log("Deleting activity with ID:", activityId);
      
      // Optimistically remove from UI
      setDailyActivities(prevActivities => prevActivities.filter(activity => activity.id !== activityId));
      
      // Then delete from backend
      await api.delete(`/activities/${activityId}`);
      console.log("Activity deleted from backend successfully");

    } catch (err) {
      console.error("Failed to delete activity:", err);
      setError("Failed to delete activity. The item was removed from the view, but may reappear on refresh if the server failed to process the deletion.");
      // Note: In a more robust implementation, we might add the activity back to the list
      // or use a more sophisticated state management to indicate the failed deletion.
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
  };  // Function to handle clicking on a calendar day
  const handleDayClick = (event, date) => {
    // Set the selected date
    setSelectedDate(date);
    
    // Always center the modal in the middle of the screen
    setModalPosition({ left: '50%', top: '50%' });
    
    // Show the modal
    setShowModal(true);
  };
  
  // Handle clicking outside the modal to close it
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modalRef.current && !modalRef.current.contains(event.target)) {
        setShowModal(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);
  
  // Handle escape key to close modal
  useEffect(() => {
    const handleEscKey = (event) => {
      if (event.key === 'Escape') {
        setShowModal(false);
      }
    };
    
    document.addEventListener('keydown', handleEscKey);
    return () => {
      document.removeEventListener('keydown', handleEscKey);
    };
  }, []);
  
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
      
      // Filter activities for the current date
      const dayActivities = dailyActivities.filter(activity => activity.date === currentDateStr);

      const isToday = 
        currentDate.getDate() === today.getDate() &&
        currentDate.getMonth() === today.getMonth() &&
        currentDate.getFullYear() === today.getFullYear();
        
      days.push(
        <div 
          key={day} 
          className={`calendar-day ${isToday ? 'today' : ''} ${currentDateStr === newActivity.date ? 'selected' : ''}`} 
          onClick={(e) => {
            // Only set the new activity date if no activities button was clicked
            if (!e.target.closest('.activity-count-button')) {
              setNewActivity({...newActivity, date: currentDateStr});
            }
          }}
        >
          <span className="day-number">{day}</span>
          {isToday && <span className="today-marker">Today</span>}
          <div className="tasks-on-day">
            {dayActivities.length > 0 && (
              <button 
                className="activity-count-button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDayClick(e, currentDateStr);
                }}
                title={`${dayActivities.length} activities on this day`}
              >
                {dayActivities.length} {dayActivities.length === 1 ? 'activity' : 'activities'} today, click to expand.
              </button>
            )}
          </div>
        </div>
      );
    }
    return days;
  };
  
  return (
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
          <p className="text-center text-muted mb-3">Click on a day in the calendar to select it</p>
            <div className="add-activity-form">
            <input 
              type="text" 
              placeholder="Activity Name (e.g., Work Block)" 
              className="input-field" 
              value={newActivity.name}
              onChange={(e) => setNewActivity({...newActivity, name: e.target.value})}
            />
            <input 
              type="date" 
              className="input-field" 
              value={newActivity.date}
              onChange={(e) => setNewActivity({...newActivity, date: e.target.value})}
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
              disabled={!newActivity.name || !newActivity.time || !newActivity.date}
            >
              Add Activity
            </button>
          </div>
            <div className="activities-list">
            {dailyActivities.length > 0 ? (              dailyActivities.map(activity => (                <div key={activity.id} className={`activity-item ${/[\u0590-\u05FF]/.test(activity.name) ? 'rtl-item' : ''}`}>
                  <div className="activity-details">
                    <strong>{activity.date} {activity.time}</strong>
                    <span className="activity-name" dir="auto" lang={/[\u0590-\u05FF]/.test(activity.name) ? 'he' : ''}>{activity.name}</span>
                  </div>                  <button 
                    className="btn btn-danger btn-small" 
                    onClick={() => handleDeleteActivity(activity.id)}
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
      </div>      {showModal && selectedDate && (
        <div 
          className="activities-modal-overlay"
          onClick={() => setShowModal(false)}
        >
          <div 
            className="activities-modal" 
            ref={modalRef}
            onClick={(e) => e.stopPropagation()}
            style={{
              top: typeof modalPosition.top === 'string' ? modalPosition.top : `${modalPosition.top}px`,
              left: typeof modalPosition.left === 'string' ? modalPosition.left : `${modalPosition.left}px`,
            }}
          >
            <div className="activities-modal-header">
              <h3>Activities for {selectedDate}</h3>
              <button 
                className="modal-close-btn" 
                onClick={() => setShowModal(false)}
                aria-label="Close modal"
              >
                ×
              </button>
            </div>
            <div className="activities-modal-content">
              {dailyActivities.filter(activity => activity.date === selectedDate).length > 0 ? (
                dailyActivities
                  .filter(activity => activity.date === selectedDate)
                  .sort((a, b) => a.time.localeCompare(b.time))
                  .map(activity => (
                    <div key={activity.id} className="modal-activity-item">
                      <div className="modal-activity-details">
                        <span className="modal-activity-time">{activity.time}</span>
                        <span className="modal-activity-name">{activity.name}</span>
                      </div>
                      <button 
                        className="btn btn-danger btn-small" 
                        onClick={() => handleDeleteActivity(activity.id)}
                      >
                        Remove
                      </button>
                    </div>
                  ))
              ) : (
                <p className="no-activities-message">No activities scheduled for this day.</p>
              )}
            </div>
            <div className="activities-modal-footer">
              <button 
                className="btn btn-primary" 
                onClick={() => {
                  setShowModal(false);
                  // Keep the selected date for adding new activity
                  setNewActivity({...newActivity, date: selectedDate});
                  // Focus the activity name input field for quick adding
                  setTimeout(() => {
                    const inputField = document.querySelector('input[placeholder="Activity Name (e.g., Work Block)"]');
                    if (inputField) inputField.focus();
                  }, 100);
                }}
              >
                Add New Activity
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CalendarPage;
