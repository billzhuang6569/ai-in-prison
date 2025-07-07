/**
 * Main App component for Project Prometheus
 */
import React, { useEffect } from 'react';
import useWorldStore from './store/worldStore';
import ControlPanel from './components/ControlPanel';
import MapView from './components/MapView';
import DetailPanel from './components/DetailPanel';
import Header from './components/Header';
import './App.css';

function App() {
  const { connect, disconnect, isConnected, worldState } = useWorldStore();
  
  useEffect(() => {
    // Connect to WebSocket on mount
    connect();
    
    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);
  
  return (
    <div className="App">
      <Header />
      
      <div className="main-content">
        <div className="left-panel">
          <ControlPanel />
        </div>
        
        <div className="center-panel">
          <MapView />
        </div>
        
        <div className="right-panel">
          <DetailPanel />
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