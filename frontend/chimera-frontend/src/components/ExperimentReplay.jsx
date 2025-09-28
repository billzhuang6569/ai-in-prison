import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import GridView from './GridView';
import SpeechBubble from './SpeechBubble';

const ExperimentReplay = ({ isVisible, onClose, experimentId }) => {
  const [replayData, setReplayData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentTick, setCurrentTick] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [selectedAgent, setSelectedAgent] = useState(null);
  
  const intervalRef = useRef(null);
  const maxTick = replayData?.metadata?.total_ticks - 1 || 0;

  useEffect(() => {
    if (isVisible && experimentId) {
      loadReplayData();
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isVisible, experimentId]);

  useEffect(() => {
    if (isPlaying && replayData) {
      intervalRef.current = setInterval(() => {
        setCurrentTick(prev => {
          if (prev >= maxTick) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1000 / playbackSpeed);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, playbackSpeed, maxTick, replayData]);

  const loadReplayData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/replay/${experimentId}`);
      if (response.ok) {
        const data = await response.json();
        setReplayData(data);
        setCurrentTick(0);
        setSelectedAgent(null);
      } else {
        console.error('Failed to load replay data:', response.statusText);
        alert('Failed to load replay data. Please try again.');
      }
    } catch (error) {
      console.error('Replay data loading error:', error);
      alert('Failed to load replay data. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleStop = () => {
    setIsPlaying(false);
    setCurrentTick(0);
  };

  const handleSpeedChange = (speed) => {
    setPlaybackSpeed(speed);
  };

  const handleTickChange = (tick) => {
    setCurrentTick(Math.max(0, Math.min(tick, maxTick)));
  };

  const handleAgentSelect = useCallback((agentId) => {
    setSelectedAgent(agentId);
  }, []);

  const getCurrentWorldState = useMemo(() => {
    if (!replayData || !replayData.ticks || currentTick >= replayData.ticks.length) {
      return null;
    }
    return replayData.ticks[currentTick];
  }, [replayData, currentTick]);

  const applySmartBubbleLayout = useCallback((bubbles) => {
    if (bubbles.length <= 1) return bubbles;
    
    const cellSize = 40;
    const cellGap = 1;
    const totalCellSize = cellSize + cellGap;
    const bubbleHeight = 60;
    const bubbleSpacing = 20;
    
    // Sort bubbles by position to process systematically
    const sortedBubbles = [...bubbles].sort((a, b) => {
      if (a.position.y !== b.position.y) return a.position.y - b.position.y;
      return a.position.x - b.position.x;
    });
    
    // Track occupied areas to prevent overlaps
    const occupiedAreas = [];
    
    return sortedBubbles.map((bubble, index) => {
      const baseX = bubble.position.x * totalCellSize + cellSize / 2;
      const baseY = bubble.position.y * totalCellSize + cellSize / 2;
      
      let offsetY = -bubbleHeight - 10; // Default: above agent
      let offsetX = 0;
      
      // Check for conflicts with existing bubbles
      let attempts = 0;
      const maxAttempts = 8;
      
      while (attempts < maxAttempts) {
        const bubbleArea = {
          x: baseX + offsetX - 100, // Bubble width ~200px
          y: baseY + offsetY - bubbleHeight/2,
          width: 200,
          height: bubbleHeight
        };
        
        // Check if this position conflicts with existing bubbles
        const hasConflict = occupiedAreas.some(area => 
          !(bubbleArea.x + bubbleArea.width < area.x || 
            bubbleArea.x > area.x + area.width ||
            bubbleArea.y + bubbleArea.height < area.y ||
            bubbleArea.y > area.y + area.height)
        );
        
        if (!hasConflict) {
          occupiedAreas.push(bubbleArea);
          break;
        }
        
        // Try different positions
        switch (attempts) {
          case 0: offsetY = bubbleHeight + 20; break; // Below agent
          case 1: offsetX = -80; offsetY = -bubbleHeight - 10; break; // Left-above
          case 2: offsetX = 80; offsetY = -bubbleHeight - 10; break; // Right-above
          case 3: offsetX = -80; offsetY = bubbleHeight + 20; break; // Left-below
          case 4: offsetX = 80; offsetY = bubbleHeight + 20; break; // Right-below
          case 5: offsetY = -bubbleHeight - 40; offsetX = 0; break; // Higher above
          case 6: offsetY = bubbleHeight + 50; offsetX = 0; break; // Lower below
          case 7: offsetX = index * 30 - 60; offsetY = -bubbleHeight - 10; break; // Spread horizontally
        }
        attempts++;
      }
      
      return {
        ...bubble,
        layoutOffset: { x: offsetX, y: offsetY }
      };
    });
  }, []);

  const getCurrentSpeechBubbles = useMemo(() => {
    const worldState = getCurrentWorldState;
    if (!worldState || !worldState.agents) return [];
    
    const bubbles = [];
    let bubbleId = 0;
    
    worldState.agents.forEach(agent => {
      if (agent.decision && agent.decision.action && agent.decision.action.type === 'say') {
        bubbles.push({
          id: bubbleId++,
          agentId: agent.id,
          content: agent.decision.action.content,
          position: agent.position,
          role: agent.role
        });
      }
    });
    
    // Apply smart layout algorithm to prevent overlaps
    return applySmartBubbleLayout(bubbles);
  }, [getCurrentWorldState, applySmartBubbleLayout]);

  const buildAgentTrajectories = useMemo(() => {
    if (!replayData || !replayData.ticks) return {};
    
    const trajectories = {};
    
    // Build trajectories from all ticks up to current tick
    for (let i = 0; i <= currentTick && i < replayData.ticks.length; i++) {
      const tickData = replayData.ticks[i];
      
      tickData.agents.forEach(agent => {
        if (!trajectories[agent.id]) {
          trajectories[agent.id] = [];
        }
        
        const position = {
          x: agent.position.x,
          y: agent.position.y,
          tick: tickData.tick
        };
        
        // Only add if position changed or it's the first position
        const lastPos = trajectories[agent.id][trajectories[agent.id].length - 1];
        if (!lastPos || lastPos.x !== position.x || lastPos.y !== position.y) {
          trajectories[agent.id].push(position);
        }
      });
    }
    
    // Debug: log trajectories with actual positions
    console.log('Built trajectories for replay:');
    Object.entries(trajectories).forEach(([agentId, trajectory]) => {
      console.log(`${agentId}:`, trajectory.map(p => `(${p.x},${p.y})`).join(' -> '));
    });
    
    return trajectories;
  }, [replayData, currentTick]);

  const getCurrentAgentData = useMemo(() => {
    const worldState = getCurrentWorldState;
    if (!worldState || !selectedAgent) return null;
    
    const agent = worldState.agents.find(a => a.id === selectedAgent);
    return agent;
  }, [getCurrentWorldState, selectedAgent]);

  if (!isVisible) return null;

  return (
    <div className="replay-overlay">
      <div className="replay-container">
        <div className="replay-header">
          <h2>Experiment Replay: {experimentId}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        {loading ? (
          <div className="loading">Loading replay data...</div>
        ) : !replayData ? (
          <div className="error">Failed to load replay data</div>
        ) : (
          <>
            <div className="replay-content">
              <div className="replay-main">
                <div className="replay-grid" style={{ position: 'relative' }}>
                  <GridView
                    worldState={getCurrentWorldState}
                    selectedAgent={selectedAgent}
                    onAgentSelect={handleAgentSelect}
                    agentTrajectories={buildAgentTrajectories}
                  />
                  
                  {/* Speech bubbles overlay */}
                  <div className="speech-bubbles-overlay" style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    pointerEvents: 'none',
                    zIndex: 300
                  }}>
                    {getCurrentSpeechBubbles.map(bubble => (
                       <SpeechBubble
                         key={`${currentTick}-${bubble.id}`}
                         content={bubble.content}
                         agentId={bubble.agentId}
                         position={bubble.position}
                         role={bubble.role}
                         bubbleId={bubble.id}
                         layoutOffset={bubble.layoutOffset}
                       />
                     ))}
                  </div>
                </div>
              </div>
              
              <div className="replay-sidebar">
                <div className="replay-info">
                  <h3>Replay Information</h3>
                  <div className="info-item">
                    <span>Current Tick:</span>
                    <span>{currentTick + 1} / {replayData.metadata.total_ticks}</span>
                  </div>
                  <div className="info-item">
                    <span>Total Agents:</span>
                    <span>{replayData.metadata.agents.length}</span>
                  </div>
                  <div className="info-item">
                    <span>Map Size:</span>
                    <span>{replayData.metadata.map_size[0]} × {replayData.metadata.map_size[1]}</span>
                  </div>
                  
                  {/* Current tick speech actions */}
                   {getCurrentSpeechBubbles.length > 0 && (
                     <div className="current-speech">
                       <h4>Current Conversations</h4>
                       {getCurrentSpeechBubbles.map(bubble => (
                         <div key={bubble.id} className="speech-item">
                           <strong style={{ color: bubble.role === 'guard' ? '#007acc' : '#d73a49' }}>
                             {bubble.agentId}:
                           </strong>
                           <span> "{bubble.content}"</span>
                         </div>
                       ))}
                     </div>
                   )}
                </div>

                {/* All agents status */}
                <div className="all-agents-status">
                  <h3>All Agents Status</h3>
                  <div className="agents-grid">
                    {getCurrentWorldState?.agents?.map(agent => (
                      <div 
                        key={agent.id} 
                        className={`agent-card ${selectedAgent === agent.id ? 'selected' : ''}`}
                        onClick={() => handleAgentSelect(agent.id)}
                      >
                        <div className="agent-card-header">
                          <span className={`agent-role ${agent.role}`}>{agent.id}</span>
                          <span className="agent-position">({agent.position.x}, {agent.position.y})</span>
                        </div>
                        <div className="agent-card-body">
                          <div className="status-row">
                            <span>Energy:</span>
                            <span>{agent.status?.energy || 'N/A'}</span>
                          </div>
                          <div className="status-row">
                            <span>Mood:</span>
                            <span>{agent.status?.mood || 'N/A'}</span>
                          </div>
                          {agent.decision && (
                            <div className="status-row">
                              <span>Action:</span>
                              <span className="action-type">{agent.decision.action?.type || 'None'}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )) || []}
                  </div>
                </div>

                {selectedAgent && getCurrentAgentData && (
                  <div className="agent-replay-info">
                    <h3>Selected Agent: {selectedAgent}</h3>
                    <div className="agent-status">
                      <div className="status-item">
                        <span>Role:</span>
                        <span className={`role-badge ${getCurrentAgentData.role}`}>
                          {getCurrentAgentData.role}
                        </span>
                      </div>
                      <div className="status-item">
                        <span>Position:</span>
                        <span>({getCurrentAgentData.position.x}, {getCurrentAgentData.position.y})</span>
                      </div>
                      <div className="status-item">
                        <span>Energy:</span>
                        <div className="energy-bar">
                          <div 
                            className="energy-fill" 
                            style={{ width: `${getCurrentAgentData.status?.energy || 0}%` }}
                          />
                          <span className="energy-text">{getCurrentAgentData.status?.energy || 'N/A'}</span>
                        </div>
                      </div>
                      <div className="status-item">
                        <span>Mood:</span>
                        <span className="mood-indicator">{getCurrentAgentData.status?.mood || 'N/A'}</span>
                      </div>
                      {getCurrentAgentData.inventory && getCurrentAgentData.inventory.length > 0 && (
                        <div className="status-item">
                          <span>Inventory:</span>
                          <span>{getCurrentAgentData.inventory.length} items</span>
                        </div>
                      )}
                    </div>
                    
                    {getCurrentAgentData.decision && (
                      <div className="agent-decision">
                        <h4>Decision Details</h4>
                        <div className="decision-thought">
                          <strong>Thought:</strong>
                          <p>{getCurrentAgentData.decision.thought}</p>
                        </div>
                        <div className="decision-action">
                          <strong>Action:</strong>
                          <div className="action-details">
                            <span className="action-type">{getCurrentAgentData.decision.action?.type || 'None'}</span>
                            {getCurrentAgentData.decision.action?.content && (
                              <div className="action-content">
                                <strong>Says:</strong> "{getCurrentAgentData.decision.action.content}"
                              </div>
                            )}
                            {getCurrentAgentData.decision.action?.target && (
                              <div className="action-target">
                                <strong>Target:</strong> ({getCurrentAgentData.decision.action.target.x}, {getCurrentAgentData.decision.action.target.y})
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="replay-controls">
              <div className="control-buttons">
                <button 
                  className="control-btn"
                  onClick={handleStop}
                  title="Stop"
                >
                  ⏹️
                </button>
                <button 
                  className="control-btn"
                  onClick={handlePlayPause}
                  title={isPlaying ? "Pause" : "Play"}
                >
                  {isPlaying ? '⏸️' : '▶️'}
                </button>
              </div>

              <div className="progress-container">
                <input
                  type="range"
                  min="0"
                  max={maxTick}
                  value={currentTick}
                  onChange={(e) => handleTickChange(parseInt(e.target.value))}
                  className="progress-slider"
                />
                <div className="progress-info">
                  Tick {currentTick + 1} of {replayData.metadata.total_ticks}
                </div>
              </div>

              <div className="speed-controls">
                <span>Speed:</span>
                {[0.5, 1, 2, 4].map(speed => (
                  <button
                    key={speed}
                    className={`speed-btn ${playbackSpeed === speed ? 'active' : ''}`}
                    onClick={() => handleSpeedChange(speed)}
                  >
                    {speed}x
                  </button>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ExperimentReplay;