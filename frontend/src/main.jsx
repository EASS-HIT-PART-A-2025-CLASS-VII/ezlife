import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css' // Main styles and CSS variables
import './styles/common.css' // Common utility classes and component base styles
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
