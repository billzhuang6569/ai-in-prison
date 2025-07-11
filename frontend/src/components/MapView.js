/**
 * Map visualization component with movement trajectories
 */
import React, { useState, useEffect } from 'react';
import useWorldStore from '../store/worldStore';
import { Icon } from '@iconify/react';
import TurnIndicator from './TurnIndicator';
import SpeechBubble from './SpeechBubble';

function MapView({ selectedItem, onItemPlace }) {
  const { worldState, selectedAgent, setSelectedAgent } = useWorldStore();
  const [agentTrajectories, setAgentTrajectories] = useState({});
  const [showTrajectories, setShowTrajectories] = useState(true);
  const [speechBubbles, setSpeechBubbles] = useState({});
  const [lastProcessedEvents, setLastProcessedEvents] = useState(new Set());
  
  // Item icon mapping for map display using Game Icons
  const itemIconMap = {
    "food": "game-icons:meal",
    "water": "game-icons:water-drop",
    "book": "game-icons:book-cover",
    "baton": "game-icons:truncheon",
    "handcuffs": "game-icons:handcuffed",
    "radio": "game-icons:radio-tower",
    "keys": "game-icons:key",
    "first_aid": "game-icons:first-aid-kit",
    "whistle": "game-icons:whistle",
    "cigarettes": "game-icons:cigarette",
    "playing_cards": "game-icons:card-play",
    "diary": "game-icons:notebook",
    "spoon": "game-icons:spoon",
    "bedsheet": "game-icons:bed",
    "soap": "game-icons:soap",
    "shiv": "game-icons:switchblade",
    "rope": "game-icons:rope-coil",
    "lockpick": "game-icons:lock-picks",
    "toolbox": "game-icons:toolbox",
    "chair": "game-icons:chair",
    "table": "game-icons:table"
  };
  
  // Function to place item on map
  const placeItemOnMap = async (x, y, item) => {
    try {
      const response = await fetch('http://localhost:24861/api/v1/items/place', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: worldState.session_id,
          x: x,
          y: y,
          item_type: item.id,
          item_name: item.name,
          item_description: item.description
        }),
      });
      
      if (response.ok) {
        console.log(`Placed ${item.name} at (${x}, ${y})`);
        onItemPlace(); // Clear selection
      } else {
        console.error('Failed to place item');
      }
    } catch (error) {
      console.error('Error placing item:', error);
    }
  };
  
  // Load and update agent movement trajectories
  useEffect(() => {
    if (!worldState?.session_id) return;
    
    // Clear cache when session changes
    setAgentTrajectories({});
    setSpeechBubbles({});
    setLastProcessedEvents(new Set());
    
    const loadTrajectories = async () => {
      try {
        const response = await fetch(`http://localhost:24861/api/v1/events?limit=200&session_id=${worldState.session_id}&event_type=move`);
        const data = await response.json();
        
        // Group movement events by agent
        const trajectories = {};
        data.events.forEach(event => {
          if (event.event_type === 'move') {
            if (!trajectories[event.agent_name]) {
              trajectories[event.agent_name] = [];
            }
            
            // Parse position from event description (e.g., "Moved to (5, 3)")
            const posMatch = event.description.match(/\((\d+),\s*(\d+)\)/);
            if (posMatch) {
              trajectories[event.agent_name].push({
                x: parseInt(posMatch[1]),
                y: parseInt(posMatch[2]),
                timestamp: event.timestamp,
                day: event.day,
                hour: event.hour,
                minute: event.minute
              });
            }
          }
        });
        
        // Keep only the latest 20 positions per agent and sort by timestamp
        Object.keys(trajectories).forEach(agentName => {
          trajectories[agentName] = trajectories[agentName]
            .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
          // 保留所有历史轨迹，不再限制数量
        });
        
        // Sync trajectory endpoints with current agent positions
        if (worldState?.agents) {
          Object.values(worldState.agents).forEach(agent => {
            const agentName = agent.name;
            if (trajectories[agentName] && trajectories[agentName].length > 0) {
              const currentPos = { x: agent.position[0], y: agent.position[1] };
              const lastTrajectoryPos = trajectories[agentName][trajectories[agentName].length - 1];
              
              // If current position differs from last trajectory point, update or add it
              if (lastTrajectoryPos.x !== currentPos.x || lastTrajectoryPos.y !== currentPos.y) {
                // Add current position as the most recent point
                trajectories[agentName].push({
                  x: currentPos.x,
                  y: currentPos.y,
                  timestamp: new Date().toISOString(),
                  day: worldState.day,
                  hour: worldState.hour,
                  minute: worldState.minute || 0
                });
                
                // 保留所有轨迹点
                // trajectories[agentName] = trajectories[agentName].slice(-20);
              }
            } else if (!trajectories[agentName]) {
              // If no trajectory exists, create one with current position
              trajectories[agentName] = [{
                x: agent.position[0],
                y: agent.position[1],
                timestamp: new Date().toISOString(),
                day: worldState.day,
                hour: worldState.hour,
                minute: worldState.minute || 0
              }];
            }
          });
        }
        
        setAgentTrajectories(trajectories);
      } catch (error) {
        console.error('Error loading trajectories:', error);
      }
    };
    
    loadTrajectories();
    
    // Refresh trajectories every 3 seconds when experiment is running (faster update)
    const interval = worldState?.is_running ? setInterval(loadTrajectories, 3000) : null;
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [worldState?.session_id, worldState?.is_running]);
  
  // Additional effect to sync trajectories whenever worldState agents change (IMMEDIATE UPDATE)
  useEffect(() => {
    if (!worldState?.agents || Object.keys(agentTrajectories).length === 0) return;
    
    const syncTrajectories = () => {
      setAgentTrajectories(prevTrajectories => {
        const updatedTrajectories = { ...prevTrajectories };
        let hasChanges = false;
        
        Object.values(worldState.agents).forEach(agent => {
          const agentName = agent.name;
          if (updatedTrajectories[agentName] && updatedTrajectories[agentName].length > 0) {
            const currentPos = { x: agent.position[0], y: agent.position[1] };
            const lastTrajectoryPos = updatedTrajectories[agentName][updatedTrajectories[agentName].length - 1];
            
            // If current position differs from last trajectory point, update it
            if (lastTrajectoryPos.x !== currentPos.x || lastTrajectoryPos.y !== currentPos.y) {
              updatedTrajectories[agentName] = [
                ...updatedTrajectories[agentName],
                {
                  x: currentPos.x,
                  y: currentPos.y,
                  timestamp: new Date().toISOString(),
                  day: worldState.day,
                  hour: worldState.hour,
                  minute: worldState.minute || 0
                }
              ]; // 保留所有轨迹点
              hasChanges = true;
              
              // Force immediate trajectory refresh from server
              setTimeout(() => {
                if (worldState?.session_id) {
                  fetch(`http://localhost:24861/api/v1/events?limit=50&session_id=${worldState.session_id}&event_type=move`)
                    .then(response => response.json())
                    .then(data => {
                      // Update trajectories with latest server data
                      const trajectories = {};
                      data.events.forEach(event => {
                        if (event.event_type === 'move') {
                          if (!trajectories[event.agent_name]) {
                            trajectories[event.agent_name] = [];
                          }
                          const posMatch = event.description.match(/\((\d+),\s*(\d+)\)/);
                          if (posMatch) {
                            trajectories[event.agent_name].push({
                              x: parseInt(posMatch[1]),
                              y: parseInt(posMatch[2]),
                              timestamp: event.timestamp,
                              day: event.day,
                              hour: event.hour,
                              minute: event.minute
                            });
                          }
                        }
                      });
                      
                      // Sort and update trajectories
                      Object.keys(trajectories).forEach(agentName => {
                        trajectories[agentName] = trajectories[agentName]
                          .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                      });
                      
                      setAgentTrajectories(prev => ({ ...prev, ...trajectories }));
                    })
                    .catch(error => console.error('Error refreshing trajectories:', error));
                }
              }, 500); // Refresh after 500ms
            }
          }
        });
        
        return hasChanges ? updatedTrajectories : prevTrajectories;
      });
    };
    
    syncTrajectories();
  }, [worldState?.agents, worldState?.day, worldState?.hour, worldState?.minute]);
  
  // 监听语言事件以显示对话气泡
  useEffect(() => {
    const checkForSpeechEvents = async () => {
      try {
        const response = await fetch(`http://localhost:24861/api/v1/events?limit=10&event_type=speech${worldState?.session_id ? `&session_id=${worldState.session_id}` : ''}`);
        const data = await response.json();
        
        if (data.events && data.events.length > 0) {
          data.events.forEach(event => {
            const eventId = `${event.id}-${event.timestamp}`;
            
            // 如果这个事件还没有处理过，并且是说话事件
            if (!lastProcessedEvents.has(eventId) && event.event_type === 'speech') {
              const agent = Object.values(worldState?.agents || {}).find(a => a.name === event.agent_name);
              
              if (agent && event.description) {
                // 提取说话内容 - 支持中英文格式
                let speechContent = '';
                // 尝试匹配英文格式: "Said to [Target]: 'Message'"
                const englishMatch = event.description.match(/Said to .+?:\s*'([^']+)'/);
                // 尝试匹配中文格式: "说："Message""
                const chineseMatch = event.description.match(/说[：:]\s*"([^"]+)"/);
                
                if (englishMatch) {
                  speechContent = englishMatch[1];
                } else if (chineseMatch) {
                  speechContent = chineseMatch[1];
                } else {
                  // 如果都不匹配，使用整个描述
                  speechContent = event.description;
                }
                
                // 显示对话气泡
                setSpeechBubbles(prev => ({
                  ...prev,
                  [agent.agent_id]: {
                    agent: agent,
                    message: speechContent,
                    position: { x: agent.position[0], y: agent.position[1] }
                  }
                }));
                
                // 标记为已处理
                setLastProcessedEvents(prev => new Set([...prev, eventId]));
                
                // 30秒后自动清除（防止重复）
                setTimeout(() => {
                  setSpeechBubbles(prev => {
                    const updated = { ...prev };
                    delete updated[agent.agent_id];
                    return updated;
                  });
                }, 30000);
              }
            }
          });
        }
      } catch (error) {
        console.error('Error checking for speech events:', error);
      }
    };
    
    if (worldState?.is_running) {
      checkForSpeechEvents();
      const interval = setInterval(checkForSpeechEvents, 2000); // 每2秒检查一次
      return () => clearInterval(interval);
    }
  }, [worldState?.is_running, worldState?.agents, lastProcessedEvents]);
  
  if (!worldState) {
    return (
      <div className="map-container">
        <div style={{ 
          textAlign: 'center',
          color: '#666',
          fontSize: '18px'
        }}>
          World not initialized
        </div>
      </div>
    );
  }
  
  const { game_map, agents } = worldState;
  
  // Create grid template - 增大地图单元格尺寸
  const cellSize = 45; // 从30px增加到45px
  const gridStyle = {
    gridTemplateColumns: `repeat(${game_map.width}, ${cellSize}px)`,
    gridTemplateRows: `repeat(${game_map.height}, ${cellSize}px)`
  };
  
  // Create cells array
  const cells = [];
  for (let y = 0; y < game_map.height; y++) {
    for (let x = 0; x < game_map.width; x++) {
      const cellKey = `${x},${y}`;
      const cellType = game_map.cells[cellKey] || 'Cell_Block';
      
      // Find agents at this position
      const agentsAtPosition = Object.values(agents).filter(
        agent => agent.position[0] === x && agent.position[1] === y
      );
      
      // Find items at this position
      const itemsAtPosition = game_map.items[cellKey] || [];
      
      cells.push(
        <div
          key={cellKey}
          className={`map-cell ${cellType}`}
          onClick={() => {
            if (selectedItem && agentsAtPosition.length === 0) {
              // Place item if one is selected and no agents are at this position
              placeItemOnMap(x, y, selectedItem);
            } else if (agentsAtPosition.length > 0) {
              // Select agent if present
              setSelectedAgent(agentsAtPosition[0].agent_id);
            }
          }}
          style={{
            cursor: selectedItem && agentsAtPosition.length === 0 ? 'crosshair' : 'pointer',
            backgroundColor: selectedItem && agentsAtPosition.length === 0 ? 'rgba(76, 175, 80, 0.3)' : undefined
          }}
          title={`(${x}, ${y}) - ${cellType}${itemsAtPosition.length > 0 ? ` - ${itemsAtPosition.length} items` : ''}`}
        >
          {/* Render items */}
          {itemsAtPosition.length > 0 && (
            <div style={{
              position: 'absolute',
              top: '1px',
              left: '1px',
              display: 'flex',
              flexWrap: 'wrap',
              gap: '1px',
              maxWidth: '28px',
              maxHeight: '14px',
              overflow: 'hidden',
              zIndex: 2
            }}>
              {itemsAtPosition.slice(0, 4).map((item, index) => (
                <div
                  key={`${item.item_id || index}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    lineHeight: '1'
                  }}
                  title={`${item.name}: ${item.description}`}
                >
                  <Icon 
                    icon={itemIconMap[item.item_type] || 'game-icons:questioned-badge'} 
                    width="8" 
                    height="8" 
                    style={{ 
                      color: '#FFD700',
                      filter: 'drop-shadow(0 0 2px rgba(0,0,0,0.8))'
                    }} 
                  />
                </div>
              ))}
              {itemsAtPosition.length > 4 && (
                <div style={{
                  fontSize: '6px',
                  color: '#fff',
                  backgroundColor: 'rgba(255,0,0,0.7)',
                  borderRadius: '2px',
                  padding: '0 1px',
                  lineHeight: '1'
                }}>
                  +{itemsAtPosition.length - 4}
                </div>
              )}
            </div>
          )}
          
          {/* Render agents */}
          {agentsAtPosition.map((agent, index) => {
            // Enhanced agent labels - separate counting for Guards and Prisoners
            const allAgents = Object.values(agents);
            const guards = allAgents.filter(a => a.role === 'Guard');
            const prisoners = allAgents.filter(a => a.role === 'Prisoner');
            
            let label;
            if (agent.role === 'Guard') {
              const guardIndex = guards.findIndex(a => a.agent_id === agent.agent_id) + 1;
              label = `G${guardIndex}`;
            } else {
              const prisonerIndex = prisoners.findIndex(a => a.agent_id === agent.agent_id) + 1;
              label = `P${prisonerIndex}`;
            }
            
            return (
              <div
                key={agent.agent_id}
                className={`agent-marker ${agent.role} ${
                  selectedAgent === agent.agent_id ? 'selected' : ''
                }`}
                style={{
                  zIndex: 10 + index
                }}
                title={`${agent.name} (${agent.role})\nHP: ${agent.hp}, Sanity: ${agent.sanity}, Hunger: ${agent.hunger}, Thirst: ${agent.thirst}\nPosition: (${agent.position[0]}, ${agent.position[1]})\nInventory: ${agent.inventory && agent.inventory.length > 0 ? agent.inventory.map(item => item.name).join(', ') : '空'}`}
              >
                {label}
              </div>
            );
          })}
        </div>
      );
    }
  }
  
  return (
    <div className="map-container-enhanced">
      <div>
        {/* 回合指示器 */}
        <TurnIndicator />
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h3 style={{ margin: 0, color: '#ecf0f1', textShadow: '1px 1px 2px rgba(0,0,0,0.8)' }}>
            🗺️ 监狱地图 ({game_map.width}×{game_map.height})
          </h3>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button
              onClick={() => setShowTrajectories(!showTrajectories)}
              style={{
                padding: '4px 8px',
                backgroundColor: showTrajectories ? '#4caf50' : '#666',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                fontSize: '11px',
                cursor: 'pointer'
              }}
            >
              {showTrajectories ? '🟢' : '⚪'} 轨迹
            </button>
            <div style={{ fontSize: '11px', color: '#ccc' }}>
              Day {worldState.day}, Hour {worldState.hour}
            </div>
          </div>
        </div>
        
        <div style={{ position: 'relative' }}>
          <div className="map-grid" style={gridStyle}>
            {cells}
          </div>
          
          {/* 对话气泡显示 */}
          {Object.entries(speechBubbles).map(([agentId, bubbleData]) => (
            <SpeechBubble
              key={agentId}
              agent={bubbleData.agent}
              message={bubbleData.message}
              position={bubbleData.position}
              onClose={() => {
                setSpeechBubbles(prev => {
                  const updated = { ...prev };
                  delete updated[agentId];
                  return updated;
                });
              }}
            />
          ))}
          
          {/* SVG overlay for trajectory lines */}
          {showTrajectories && (
            <svg
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: `${game_map.width * (cellSize + 1)}px`, // cellSize + 1px gap
                height: `${game_map.height * (cellSize + 1)}px`,
                pointerEvents: 'none',
                zIndex: 1
              }}
            >
              {Object.entries(agentTrajectories).map(([agentName, trajectory]) => {
                const agent = Object.values(agents).find(a => a.name === agentName);
                if (!agent) return null;
                
                const pathColor = agent.role === 'Guard' ? '#0066cc' : '#cc6600';
                
                // Ensure trajectory ends at current agent position
                const currentPos = { x: agent.position[0], y: agent.position[1] };
                let adjustedTrajectory = [...trajectory];
                
                if (trajectory.length > 0) {
                  const lastPoint = trajectory[trajectory.length - 1];
                  if (lastPoint.x !== currentPos.x || lastPoint.y !== currentPos.y) {
                    adjustedTrajectory = [...trajectory, currentPos];
                  }
                } else {
                  adjustedTrajectory = [currentPos];
                }
                
                if (adjustedTrajectory.length < 2) return null;
                
                // Create path data using adjusted trajectory
                const pathData = adjustedTrajectory.map((point, index) => {
                  const x = point.x * (cellSize + 1) + cellSize/2; // Cell center
                  const y = point.y * (cellSize + 1) + cellSize/2;
                  return index === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
                }).join(' ');
                
                return (
                  <g key={agentName}>
                    {/* Main trajectory line */}
                    <path
                      d={pathData}
                      stroke={pathColor}
                      strokeWidth="2"
                      fill="none"
                      opacity="0.6"
                      strokeDasharray="3,2"
                    />
                    
                    {/* Direction arrows */}
                    {adjustedTrajectory.slice(1).map((point, index) => {
                      const prevPoint = adjustedTrajectory[index];
                      const dx = point.x - prevPoint.x;
                      const dy = point.y - prevPoint.y;
                      
                      if (dx === 0 && dy === 0) return null;
                      
                      const x = point.x * (cellSize + 1) + cellSize/2;
                      const y = point.y * (cellSize + 1) + cellSize/2;
                      const angle = Math.atan2(dy, dx) * 180 / Math.PI;
                      
                      return (
                        <g
                          key={`arrow-${index}`}
                          transform={`translate(${x}, ${y}) rotate(${angle})`}
                        >
                          <polygon
                            points="-3,0 3,2 3,-2"
                            fill={pathColor}
                            opacity="0.8"
                          />
                        </g>
                      );
                    })}
                    
                    {/* Start point marker */}
                    {adjustedTrajectory.length > 0 && (
                      <circle
                        cx={adjustedTrajectory[0].x * (cellSize + 1) + cellSize/2}
                        cy={adjustedTrajectory[0].y * (cellSize + 1) + cellSize/2}
                        r="3"
                        fill={pathColor}
                        opacity="0.8"
                        stroke="white"
                        strokeWidth="1"
                      />
                    )}
                    
                    {/* End point marker (current position) */}
                    <circle
                      cx={currentPos.x * (cellSize + 1) + cellSize/2}
                      cy={currentPos.y * (cellSize + 1) + cellSize/2}
                      r="4"
                      fill={pathColor}
                      opacity="1"
                      stroke="white"
                      strokeWidth="2"
                    />
                  </g>
                );
              })}
            </svg>
          )}
        </div>
        
        <div style={{ 
          marginTop: '20px',
          textAlign: 'center',
          fontSize: '13px',
          color: '#ccc'
        }}>
          <div style={{ marginBottom: '8px' }}>
            <span style={{ color: '#4a4a4a', backgroundColor: '#4a4a4a', padding: '3px 6px', margin: '3px', borderRadius: '3px' }}>■</span> 牢房区域
            <span style={{ color: '#8B4513', backgroundColor: '#8B4513', padding: '3px 6px', margin: '3px', borderRadius: '3px' }}>■</span> 食堂
            <span style={{ color: '#228B22', backgroundColor: '#228B22', padding: '3px 6px', margin: '3px', borderRadius: '3px' }}>■</span> 院子
            <span style={{ color: '#800000', backgroundColor: '#800000', padding: '3px 6px', margin: '3px', borderRadius: '3px' }}>■</span> 禁闭室
            <span style={{ color: '#000080', backgroundColor: '#000080', padding: '3px 6px', margin: '3px', borderRadius: '3px' }}>■</span> 警卫室
          </div>
          <div style={{ marginTop: '10px' }}>
            <span style={{ color: '#0066cc', backgroundColor: '#0066cc', padding: '3px 6px', margin: '3px', borderRadius: '50%', fontSize: '11px' }}>G1</span> 狱警
            <span style={{ color: '#cc6600', backgroundColor: '#cc6600', padding: '3px 6px', margin: '3px', borderRadius: '50%', fontSize: '11px' }}>P1</span> 囚犯
            {showTrajectories && (
              <span style={{ color: '#888', fontSize: '11px', marginLeft: '15px' }}>
                ━━━ 移动轨迹 (所有历史路径)
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default MapView;