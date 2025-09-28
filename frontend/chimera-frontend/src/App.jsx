import React, { useState, useEffect, useRef, useMemo } from 'react';
import './App.css';
import ControlBar from './components/ControlBar';
import GridView from './components/GridView';
import InfoPanel from './components/InfoPanel';
import ExperimentConfig from './components/ExperimentConfig';
import ExperimentHistory from './components/ExperimentHistory';
import ExperimentReplay from './components/ExperimentReplay';
import useWebSocket from './hooks/useWebSocket';

function App() {
  const [worldState, setWorldState] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [agentLogs, setAgentLogs] = useState({});
  const [agentTrajectories, setAgentTrajectories] = useState({});
  const [simulationStatus, setSimulationStatus] = useState({
    isRunning: false,
    isPaused: true,
    tick: 0,
    speed: 1.0,
    experimentId: null,
    experimentStartTime: null
  });
  const [showExperimentConfig, setShowExperimentConfig] = useState(false);
  const [showExperimentHistory, setShowExperimentHistory] = useState(false);
  const [showExperimentReplay, setShowExperimentReplay] = useState(false);
  const [replayExperimentId, setReplayExperimentId] = useState(null);

  // Use ref to prevent infinite reconnection loops
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  // WebSocket connection with stable configuration
  const wsConfig = useMemo(() => ({
    onMessage: (message) => {
      try {
        const data = JSON.parse(message.data);
        
        switch (data.type) {
          case 'world_update':
            setWorldState(data.data);
            setSimulationStatus(prev => ({
              ...prev,
              tick: data.data.tick
            }));
            
            // Update agent trajectories
            setAgentTrajectories(prev => {
              const newTrajectories = { ...prev };
              data.data.agents.forEach(agent => {
                if (!newTrajectories[agent.id]) {
                  newTrajectories[agent.id] = [];
                }
                
                // Add current position to trajectory
                const currentPos = { x: agent.position.x, y: agent.position.y, tick: data.data.tick };
                const trajectory = newTrajectories[agent.id];
                
                // Only add if position changed or it's the first position
                if (trajectory.length === 0 || 
                    trajectory[trajectory.length - 1].x !== currentPos.x || 
                    trajectory[trajectory.length - 1].y !== currentPos.y) {
                  trajectory.push(currentPos);
                  
                  // Keep only last 10 positions for performance
                  if (trajectory.length > 10) {
                    trajectory.shift();
                  }
                }
              });
              
              // Debug: log trajectories to console
              console.log('Agent trajectories updated:', newTrajectories);
              return newTrajectories;
            });
            
            reconnectAttempts.current = 0; // Reset on successful message
            
            // Force re-render of grid view to show position updates
            setSelectedAgent(prev => prev); // Trigger re-render
            break;
            
          case 'experiment_started':
            setSimulationStatus(prev => ({
              ...prev,
              experimentId: data.experiment_id,
              experimentStartTime: data.start_time,
              isRunning: true,
              isPaused: false
            }));
            setWorldState(data.world_state);
            // Clear previous experiment logs and trajectories
            setAgentLogs({});
            setAgentTrajectories({});
            localStorage.removeItem('chimera_agent_logs');
            break;
            
          case 'experiment_ended':
            setSimulationStatus(prev => ({
              ...prev,
              isRunning: false,
              isPaused: true
            }));
            break;
            
          case 'agent_log_update':
            setAgentLogs(prev => {
              const newLogs = {
                ...prev,
                [data.agent_id]: [
                  ...(prev[data.agent_id] || []),
                  {
                    timestamp: new Date().toISOString(),
                    thought: data.data.thought || "No thought recorded",
                    action: data.data.action
                  }
                ].slice(-20) // Keep last 20 logs instead of 10
              };
              
              // Save to localStorage for persistence
              localStorage.setItem('chimera_agent_logs', JSON.stringify(newLogs));
              return newLogs;
            });
            
            // Force re-render of selected agent panel
            if (data.agent_id === selectedAgent) {
              setSelectedAgent(null);
              setTimeout(() => setSelectedAgent(data.agent_id), 10);
            }
            break;
            
          case 'control_ack':
            console.log('Control acknowledged:', data);
            break;
            
          case 'focus_ack':
            console.log('Agent focus acknowledged:', data);
            break;
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
      reconnectAttempts.current += 1;
      
      if (reconnectAttempts.current >= maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
      }
    }
  }), []); // Empty dependency array to prevent recreation

  const { sendMessage, connectionStatus } = useWebSocket('ws://localhost:8000/ws', wsConfig);

  // Load agent logs from localStorage on component mount
  useEffect(() => {
    const savedLogs = localStorage.getItem('chimera_agent_logs');
    if (savedLogs) {
      try {
        setAgentLogs(JSON.parse(savedLogs));
      } catch (error) {
        console.error('Failed to load saved agent logs:', error);
      }
    }
    
    // Fetch current simulation status from backend on mount
    fetchSimulationStatus();
  }, []);

  const fetchSimulationStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/status');
      if (response.ok) {
        const status = await response.json();
        setSimulationStatus(prev => ({
          ...prev,
          isRunning: status.is_running,
          isPaused: status.is_paused,
          tick: status.tick,
          speed: status.tick_speed,
          experimentId: status.experiment_id,
          experimentStartTime: status.experiment_start_time
        }));
        
        // If there's an active experiment, also fetch world state
        if (status.is_running || status.experiment_id) {
          fetchWorldState();
        }
      }
    } catch (error) {
      console.error('Failed to fetch simulation status:', error);
      // Don't show error to user, just log it
    }
  };

  const fetchWorldState = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/world_state');
      if (response.ok) {
        const worldState = await response.json();
        setWorldState(worldState);
      }
    } catch (error) {
      console.error('Failed to fetch world state:', error);
    }
  };

  const handleControlCommand = (command, value = null) => {
    // Show configuration modal for new experiment
    if (command === 'play' && !simulationStatus.isRunning && !simulationStatus.experimentId) {
      setShowExperimentConfig(true);
      return;
    }
    
    // Show configuration modal for explicit new experiment request
    if (command === 'new_experiment') {
      setShowExperimentConfig(true);
      return;
    }
    
    // Show experiment history
    if (command === 'show_history') {
      setShowExperimentHistory(true);
      return;
    }
    
    const message = {
      type: 'control_simulation',
      command: command
    };
    
    if (value !== null) {
      message.value = value;
    }
    
    sendMessage(message);
    
    // Update local status optimistically
    setSimulationStatus(prev => {
      switch (command) {
        case 'play':
          return { ...prev, isRunning: true, isPaused: false };
        case 'pause':
          return { ...prev, isPaused: true };
        case 'resume':
          return { ...prev, isPaused: false };
        case 'stop':
          return { ...prev, isRunning: false, isPaused: true };
        case 'set_speed':
          return { ...prev, speed: value };
        default:
          return prev;
      }
    });
  };

  const handleStartExperiment = (experimentConfig) => {
    // Send experiment configuration to backend
    sendMessage({
      type: 'start_experiment',
      config: experimentConfig
    });
  };

  const handleLoadExperiment = (experimentId) => {
    // Send load experiment request to backend
    sendMessage({
      type: 'load_experiment',
      experiment_id: experimentId
    });
    setShowExperimentHistory(false);
  };

  const handleReplayExperiment = (experimentId) => {
    // Open replay modal with experiment data
    setReplayExperimentId(experimentId);
    setShowExperimentReplay(true);
    setShowExperimentHistory(false);
  };

  const handleAgentSelect = (agentId) => {
    setSelectedAgent(agentId);
    
    // Notify server about agent focus
    sendMessage({
      type: 'focus_agent',
      agent_id: agentId
    });
  };

  return (
    <div className="app">
      <div className="app-header">
        <ControlBar
          simulationStatus={simulationStatus}
          connectionStatus={connectionStatus}
          onControlCommand={handleControlCommand}
        />
      </div>
      
      <div className="app-body">
        <div className="main-view">
          <GridView
            worldState={worldState}
            selectedAgent={selectedAgent}
            onAgentSelect={handleAgentSelect}
            agentTrajectories={agentTrajectories}
          />
        </div>
        
        <div className="info-panel">
          <InfoPanel
            selectedAgent={selectedAgent}
            worldState={worldState}
            agentLogs={agentLogs[selectedAgent] || []}
          />
        </div>
      </div>

      {/* Experiment Configuration Modal */}
      <ExperimentConfig
        isVisible={showExperimentConfig}
        onClose={() => setShowExperimentConfig(false)}
        onStartExperiment={handleStartExperiment}
      />

      {/* Experiment History Modal */}
      <ExperimentHistory
        isVisible={showExperimentHistory}
        onClose={() => setShowExperimentHistory(false)}
        onLoadExperiment={handleLoadExperiment}
        onReplayExperiment={handleReplayExperiment}
      />

      {/* Experiment Replay Modal */}
      <ExperimentReplay
        isVisible={showExperimentReplay}
        onClose={() => {
          setShowExperimentReplay(false);
          setReplayExperimentId(null);
        }}
        experimentId={replayExperimentId}
      />
    </div>
  );
}

export default App;
