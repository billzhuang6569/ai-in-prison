import React, { useState } from 'react';

const ExperimentConfig = ({ onStartExperiment, isVisible, onClose }) => {
  const [config, setConfig] = useState({
    guardCount: 2,
    prisonerCount: 2,
    mapSize: [10, 10],
    tickDuration: 1.0,
    maxTicks: 100
  });

  const [agentConfigs, setAgentConfigs] = useState([
    {
      id: 'guard_01',
      role: 'guard',
      personality: 'Strict and authoritative, believes in maintaining order through discipline.',
      position: { x: 2, y: 2 }
    },
    {
      id: 'guard_02',
      role: 'guard',
      personality: 'More lenient and empathetic, tries to understand prisoners\' perspectives.',
      position: { x: 7, y: 2 }
    },
    {
      id: 'prisoner_01',
      role: 'prisoner',
      personality: 'Rebellious and defiant, challenges authority at every opportunity.',
      position: { x: 2, y: 7 }
    },
    {
      id: 'prisoner_02',
      role: 'prisoner',
      personality: 'Quiet and observant, tries to avoid conflict and follow rules.',
      position: { x: 7, y: 7 }
    }
  ]);

  const handleConfigChange = (field, value) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAgentConfigChange = (index, field, value) => {
    setAgentConfigs(prev => {
      const newConfigs = [...prev];
      newConfigs[index] = {
        ...newConfigs[index],
        [field]: value
      };
      return newConfigs;
    });
  };

  const addAgent = (role) => {
    const newId = `${role}_${String(agentConfigs.filter(a => a.role === role).length + 1).padStart(2, '0')}`;
    const newAgent = {
      id: newId,
      role: role,
      personality: role === 'guard' ? 'Professional and dutiful guard.' : 'Cautious prisoner trying to survive.',
      position: { x: Math.floor(Math.random() * 8) + 1, y: Math.floor(Math.random() * 8) + 1 }
    };
    setAgentConfigs(prev => [...prev, newAgent]);
  };

  const removeAgent = (index) => {
    setAgentConfigs(prev => prev.filter((_, i) => i !== index));
  };

  const handleStartExperiment = () => {
    const experimentConfig = {
      ...config,
      agents: agentConfigs
    };
    onStartExperiment(experimentConfig);
    onClose();
  };

  if (!isVisible) return null;

  return (
    <div className="experiment-config-overlay">
      <div className="experiment-config-modal">
        <div className="config-header">
          <h2>Configure New Experiment</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <div className="config-content">
          {/* Basic Settings */}
          <div className="config-section">
            <h3>Basic Settings</h3>
            <div className="config-row">
              <label>Map Size:</label>
              <input
                type="number"
                value={config.mapSize[0]}
                onChange={(e) => handleConfigChange('mapSize', [parseInt(e.target.value), config.mapSize[1]])}
                min="5"
                max="20"
              />
              ×
              <input
                type="number"
                value={config.mapSize[1]}
                onChange={(e) => handleConfigChange('mapSize', [config.mapSize[0], parseInt(e.target.value)])}
                min="5"
                max="20"
              />
            </div>
            
            <div className="config-row">
              <label>Tick Duration (seconds):</label>
              <input
                type="number"
                step="0.1"
                value={config.tickDuration}
                onChange={(e) => handleConfigChange('tickDuration', parseFloat(e.target.value))}
                min="0.1"
                max="10"
              />
            </div>
            
            <div className="config-row">
              <label>Max Ticks:</label>
              <input
                type="number"
                value={config.maxTicks}
                onChange={(e) => handleConfigChange('maxTicks', parseInt(e.target.value))}
                min="10"
                max="1000"
              />
            </div>
          </div>

          {/* Agent Configuration */}
          <div className="config-section">
            <h3>Agents ({agentConfigs.length})</h3>
            
            <div className="agent-controls">
              <button className="add-agent-btn guard" onClick={() => addAgent('guard')}>
                + Add Guard
              </button>
              <button className="add-agent-btn prisoner" onClick={() => addAgent('prisoner')}>
                + Add Prisoner
              </button>
            </div>

            <div className="agents-list">
              {agentConfigs.map((agent, index) => (
                <div key={index} className="agent-config-item">
                  <div className="agent-config-header">
                    <span className={`agent-role ${agent.role}`}>{agent.role}</span>
                    <span className="agent-id">{agent.id}</span>
                    <button className="remove-agent-btn" onClick={() => removeAgent(index)}>×</button>
                  </div>
                  
                  <div className="agent-config-details">
                    <div className="config-row">
                      <label>ID:</label>
                      <input
                        type="text"
                        value={agent.id}
                        onChange={(e) => handleAgentConfigChange(index, 'id', e.target.value)}
                      />
                    </div>
                    
                    <div className="config-row">
                      <label>Position:</label>
                      <input
                        type="number"
                        value={agent.position.x}
                        onChange={(e) => handleAgentConfigChange(index, 'position', { ...agent.position, x: parseInt(e.target.value) })}
                        min="1"
                        max={config.mapSize[0] - 2}
                      />
                      ,
                      <input
                        type="number"
                        value={agent.position.y}
                        onChange={(e) => handleAgentConfigChange(index, 'position', { ...agent.position, y: parseInt(e.target.value) })}
                        min="1"
                        max={config.mapSize[1] - 2}
                      />
                    </div>
                    
                    <div className="config-row">
                      <label>Personality:</label>
                      <textarea
                        value={agent.personality}
                        onChange={(e) => handleAgentConfigChange(index, 'personality', e.target.value)}
                        rows="2"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="config-footer">
          <button className="config-button secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="config-button primary" onClick={handleStartExperiment}>
            Start Experiment
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExperimentConfig;