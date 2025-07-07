/**
 * Control Panel component for experiment controls
 */
import React from 'react';
import useWorldStore from '../store/worldStore';

function ControlPanel() {
  const { worldState, startExperiment, stopExperiment, isConnected } = useWorldStore();
  
  const handleStart = () => {
    startExperiment();
  };
  
  const handleStop = () => {
    stopExperiment();
  };
  
  const isRunning = worldState?.is_running || false;
  
  return (
    <div className="panel">
      <h2>Experiment Controls</h2>
      
      <div className="form-group">
        <button 
          className="btn btn-success" 
          onClick={handleStart}
          disabled={!isConnected || isRunning}
        >
          Start Experiment
        </button>
        
        <button 
          className="btn btn-danger" 
          onClick={handleStop}
          disabled={!isConnected || !isRunning}
        >
          Stop Experiment
        </button>
      </div>
      
      <h3>Global Status</h3>
      {worldState && (
        <div>
          <p>Day: {worldState.day}</p>
          <p>Hour: {worldState.hour}</p>
          <p>Agents: {Object.keys(worldState.agents).length}</p>
          <p>Status: {isRunning ? 'Running' : 'Stopped'}</p>
        </div>
      )}
      
      <h3>Agent Overview</h3>
      {worldState && (
        <div>
          {Object.values(worldState.agents).map(agent => (
            <div key={agent.agent_id} style={{ 
              marginBottom: '10px',
              padding: '8px',
              backgroundColor: '#333',
              borderRadius: '4px',
              fontSize: '12px'
            }}>
              <div style={{ fontWeight: 'bold' }}>
                {agent.name} ({agent.role})
              </div>
              <div style={{ color: '#ccc' }}>
                HP: {agent.hp} | Sanity: {agent.sanity} | 
                Pos: ({agent.position[0]}, {agent.position[1]})
              </div>
              {agent.status_tags.length > 0 && (
                <div className="status-tags">
                  {agent.status_tags.map(tag => (
                    <span key={tag} className="status-tag">{tag}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      
      <h3>Recent Events</h3>
      <div className="event-log">
        {worldState?.event_log.slice(-20).reverse().map((event, index) => (
          <div key={index} className="event-log-item">
            {event}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ControlPanel;