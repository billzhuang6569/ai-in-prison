/**
 * Main App component for Project Prometheus - Redesigned Layout
 */
import React, { useEffect, useState } from 'react';
import useWorldStore from './store/worldStore';
import ExperimentControl from './components/ExperimentControl';
import EventTable from './components/EventTable';
import AgentPreview from './components/AgentPreview';
import MapView from './components/MapView';
import AgentCards from './components/AgentCards';
import AgentDetails from './components/AgentDetails';
import Header from './components/Header';
import SessionHistoryPanel from './components/SessionHistoryPanel';
import ItemToolbar from './components/ItemToolbar';
import ExperimentMilestones from './components/ExperimentMilestones';
import './App.css';

function App() {
  const { connect, disconnect, isConnected, worldState } = useWorldStore();
  const [showSessionHistory, setShowSessionHistory] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  
  // Handle ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && showSessionHistory) {
        setShowSessionHistory(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showSessionHistory]);
  
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
      <Header onSessionHistoryClick={() => setShowSessionHistory(true)} />
      
      {/* Session History Modal */}
      {showSessionHistory && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setShowSessionHistory(false);
            }
          }}
        >
          <div style={{
            width: '95%',
            height: '90%',
            backgroundColor: '#1a1a1a',
            borderRadius: '8px',
            position: 'relative',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)'
          }}>
            {/* Close Button */}
            <button
              onClick={() => setShowSessionHistory(false)}
              style={{
                position: 'absolute',
                top: '10px',
                right: '15px',
                backgroundColor: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '50%',
                width: '30px',
                height: '30px',
                cursor: 'pointer',
                fontSize: '16px',
                zIndex: 1001,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              title="关闭"
            >
              ×
            </button>
            
            <SessionHistoryPanel />
          </div>
        </div>
      )}
      
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
          <MapView selectedItem={selectedItem} onItemPlace={() => setSelectedItem(null)} />
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
      
      {/* Item Toolbar */}
      <ItemToolbar 
        selectedItem={selectedItem}
        onItemSelect={setSelectedItem}
        onClearSelection={() => setSelectedItem(null)}
      />
      
      {/* Experiment Milestones */}
      <ExperimentMilestones />
    </div>
  );
}

export default App;