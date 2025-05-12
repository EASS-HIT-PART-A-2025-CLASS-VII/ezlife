import "./TaskPage.css";

export default function TaskPage({ tasks, onToggleTask, onDeleteTask }) {
  return (
    <div className="taskpage-container">
      <header className="taskpage-header">
        <h1>Your Tasks</h1>
        <p>Manage your tasks efficiently and stay organized.</p>
      </header>
      <ul className="task-list">
        {tasks.map((task) => (
          <li key={task.id} className={`task-item ${task.completed ? "completed" : ""}`}>
            <span>{task.description}</span>
            <div className="task-actions">
              <button onClick={() => onToggleTask(task.id)} className="btn-toggle">
                {task.completed ? "Undo" : "Complete"}
              </button>
              <button onClick={() => onDeleteTask(task.id)} className="btn-delete">Delete</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
