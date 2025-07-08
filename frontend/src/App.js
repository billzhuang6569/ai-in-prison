/**
 * Main App component for Project Prometheus - Redesigned Layout
 */
import React, { useEffect } from 'react';
import useWorldStore from './store/worldStore';
import ExperimentControl from './components/ExperimentControl';
import EventTable from './components/EventTable';
import AgentPreview from './components/AgentPreview';
import MapView from './components/MapView';
import AgentCards from './components/AgentCards';
import AgentDetails from './components/AgentDetails';
import Header from './components/Header';
import './App.css';

function App() {
  const { connect, disconnect, isConnected, worldState } = useWorldStore();
  
  useEffect(() => {
    // Suppress ResizeObserver errors
    const originalError = console.error;
    console.error = (...args) => {
      if (args[0]?.includes?.('ResizeObserver loop completed')) {
        return;
      }
      originalError(...args);
    };
    
    // Connect to WebSocket on mount
    connect();
    
    // Cleanup on unmount
    return () => {
      disconnect();
      console.error = originalError;
    };
  }, [connect, disconnect]);
  
  return (
    <div className="App">
      <Header />
      
      <div className="main-content">
        {/* Left Column */}
        <div className="left-column">
          <div className="left-top">
            <ExperimentControl />
          </div>
          <div className="left-bottom">
            <EventTable />
          </div>
        </div>
        
        {/* Left Sidebar */}
        <div className="left-sidebar">
          <AgentPreview />
        </div>
        
        {/* Center Panel */}
        <div className="center-panel">
          <MapView />
        </div>
        
        {/* Right Panel */}
        <div className="right-panel">
          <div className="right-top">
            <AgentCards />
          </div>
          <div className="right-bottom">
            <AgentDetails />
          </div>
        </div>
      </div>
      
      <div className="status-bar">
        <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '● Connected' : '● Disconnected'}
        </span>
        {worldState && (
          <span className="world-info">
            Day {worldState.day}, Hour {worldState.hour} | 
            {worldState.is_running ? ' Running' : ' Stopped'} | 
            {Object.keys(worldState.agents).length} Agents
          </span>
        )}
      </div>
    </div>
  );
}

export default App;