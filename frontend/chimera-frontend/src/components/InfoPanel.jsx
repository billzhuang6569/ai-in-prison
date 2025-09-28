import React from 'react';

const InfoPanel = ({ selectedAgent, worldState, agentLogs }) => {
  if (!selectedAgent || !worldState) {
    return (
      <div className="info-panel-content">
        <div className="no-selection">
          <h3>No Agent Selected</h3>
          <p>Click on an agent in the grid to view their details and inner thoughts.</p>
        </div>
      </div>
    );
  }

  // Find the selected agent's data
  const agentData = worldState.agents.find(agent => agent.id === selectedAgent);
  
  if (!agentData) {
    return (
      <div className="info-panel-content">
        <div className="no-selection">
          <h3>Agent Not Found</h3>
          <p>The selected agent could not be found in the current world state.</p>
        </div>
      </div>
    );
  }

  const formatPosition = (position) => {
    return `(${position.x}, ${position.y})`;
  };

  const formatStatus = (status) => {
    if (!status || typeof status !== 'object') return 'Unknown';
    
    // Extract mood information if available
    const mood = status.mood;
    if (mood && typeof mood === 'object') {
      const moodType = mood.type || 'neutral';
      const intensity = mood.intensity || 0;
      
      if (intensity === 0) {
        return 'Neutral';
      } else if (intensity < 30) {
        return `Slightly ${moodType}`;
      } else if (intensity < 60) {
        return `Moderately ${moodType}`;
      } else {
        return `Very ${moodType}`;
      }
    }
    
    // Fallback to old format
    return Object.entries(status)
      .map(([key, value]) => `${key}: ${value}`)
      .join(', ');
  };

  const getMoodEmoji = (status) => {
    if (!status || !status.mood) return '😐';
    
    const moodType = status.mood.type || 'neutral';
    const intensity = status.mood.intensity || 0;
    
    if (intensity < 20) return '😐';
    
    const emojiMap = {
      'happy': '😊',
      'angry': '😠',
      'fearful': '😨',
      'sad': '😢',
      'excited': '🤩',
      'bored': '😴',
      'anxious': '😰',
      'satisfied': '😌',
      'frustrated': '😤',
      'exhausted': '😵',
      'tired': '😪',
      'energetic': '⚡'
    };
    
    return emojiMap[moodType] || '😐';
  };

  const getInventoryItems = (worldState, agentId) => {
    const agent = worldState.agents.find(a => a.id === agentId);
    if (!agent || !agent.inventory) return [];
    
    return worldState.objects?.filter(obj => 
      agent.inventory.includes(obj.id)
    ) || [];
  };

  const getItemEmoji = (itemType) => {
    const emojiMap = {
      'Food': '🍞',
      'Readable': '📜',
      'Key': '🗝️',
      'Weapon': '🗡️',
      'Consumable': '💊'
    };
    return emojiMap[itemType] || '📦';
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const formatAction = (action) => {
    if (!action) return 'No action';
    
    switch (action.type) {
      case 'move':
        const target = action.target || {};
        return `Move to (${target.x || '?'}, ${target.y || '?'})`;
      case 'wait':
        return 'Wait and observe';
      case 'say':
        return `Say: "${action.content || ''}"`;
      default:
        return `${action.type} action`;
    }
  };

  return (
    <div className="info-panel-content">
      {/* Agent Details Section */}
      <div className="info-section">
        <h3>Agent Details</h3>
        <div className="agent-details">
          <div className="detail-row">
            <span className="detail-label">ID:</span>
            <span className="detail-value">{agentData.id}</span>
          </div>
          
          <div className="detail-row">
            <span className="detail-label">Role:</span>
            <span className={`agent-role ${agentData.role}`}>
              {agentData.role}
            </span>
          </div>
          
          <div className="detail-row">
            <span className="detail-label">Position:</span>
            <span className="detail-value">{formatPosition(agentData.position)}</span>
          </div>
          
          <div className="detail-row">
            <span className="detail-label">Mood:</span>
            <span className="detail-value mood-display">
              {getMoodEmoji(agentData.status)} {formatStatus(agentData.status)}
            </span>
          </div>
          
          <div className="detail-row">
            <span className="detail-label">Energy:</span>
            <span className="detail-value">
              <div className="energy-bar">
                <div 
                  className="energy-fill" 
                  style={{width: `${agentData.status?.energy || 100}%`}}
                ></div>
                <span className="energy-text">{agentData.status?.energy || 100}/100</span>
              </div>
            </span>
          </div>
          
          {agentData.last_utterance && (
            <div className="detail-row">
              <span className="detail-label">Last Said:</span>
              <span className="detail-value">"{agentData.last_utterance}"</span>
            </div>
          )}
          
          {agentData.inventory && agentData.inventory.length > 0 && (
            <div className="detail-row">
              <span className="detail-label">Inventory:</span>
              <div className="inventory-items">
                {getInventoryItems(worldState, agentData.id).map((item, index) => (
                  <div key={index} className="inventory-item" title={item.description}>
                    {getItemEmoji(item.type)} {item.name}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Inner Monologue Section */}
      <div className="info-section inner-monologue">
        <h3>Inner Monologue</h3>
        <div className="monologue-content">
          {agentLogs.length === 0 ? (
            <div className="no-thoughts">
              <p>No thoughts recorded yet...</p>
              <p>The agent's inner monologue will appear here as they make decisions.</p>
            </div>
          ) : (
            <div className="thoughts-list">
              {agentLogs.slice().reverse().map((log, index) => (
                <div key={index} className="thought-entry">
                  <div className="thought-header">
                    <div className="thought-timestamp">
                      Tick {worldState?.tick - index || 'Unknown'} - {formatTimestamp(log.timestamp)}
                    </div>
                  </div>
                  
                  {log.thought && log.thought !== "No thought recorded" && (
                    <div className="thought-section">
                      <div className="section-label">💭 Thought Process:</div>
                      <div className="thought-text">
                        {log.thought}
                      </div>
                    </div>
                  )}
                  
                  <div className="action-section">
                    <div className="section-label">⚡ Action Taken:</div>
                    <div className="thought-action">
                      {formatAction(log.action)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Current Action Section */}
      <div className="info-section">
        <h3>Last Action</h3>
        <div className="agent-details">
          {agentLogs.length > 0 ? (
            <div className="detail-row">
              <span className="detail-label">Latest:</span>
              <span className="detail-value">
                {formatAction(agentLogs[agentLogs.length - 1].action)}
              </span>
            </div>
          ) : (
            <div className="detail-row">
              <span className="detail-label">From World State:</span>
              <span className="detail-value">
                {agentData.last_utterance ? `Said: "${agentData.last_utterance}"` : 'No recent action'}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InfoPanel;