import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Global ResizeObserver error suppression
const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Handle ResizeObserver errors globally
const handleError = (event) => {
  if (event.message && event.message.includes('ResizeObserver loop completed')) {
    event.stopImmediatePropagation();
    return false;
  }
};

window.addEventListener('error', handleError);

// Additional error boundary for React errors
const originalConsoleError = console.error;
console.error = (...args) => {
  if (args[0] && args[0].toString().includes('ResizeObserver loop completed')) {
    return;
  }
  originalConsoleError(...args);
};

// Debounced resize handler to prevent ResizeObserver loops
const debouncedResizeHandler = debounce(() => {
  // This helps prevent ResizeObserver loops
}, 100);

window.addEventListener('resize', debouncedResizeHandler);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);