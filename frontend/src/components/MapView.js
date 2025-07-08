/**
 * Map visualization component with movement trajectories
 */
import React, { useState, useEffect } from 'react';
import useWorldStore from '../store/worldStore';

function MapView() {
  const { worldState, selectedAgent, setSelectedAgent } = useWorldStore();
  const [agentTrajectories, setAgentTrajectories] = useState({});
  const [showTrajectories, setShowTrajectories] = useState(true);
  
  // Load and update agent movement trajectories
  useEffect(() => {
    if (!worldState?.session_id) return;
    
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
            .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
            .slice(-20); // Keep last 20 positions
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
                
                // Keep only the latest 20 positions
                trajectories[agentName] = trajectories[agentName].slice(-20);
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
    
    // Refresh trajectories every 10 seconds when experiment is running
    const interval = worldState?.is_running ? setInterval(loadTrajectories, 10000) : null;
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [worldState?.session_id, worldState?.is_running]);
  
  // Additional effect to sync trajectories whenever worldState agents change
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
              ].slice(-20); // Keep only latest 20
              hasChanges = true;
            }
          }
        });
        
        return hasChanges ? updatedTrajectories : prevTrajectories;
      });
    };
    
    syncTrajectories();
  }, [worldState?.agents, worldState?.day, worldState?.hour, worldState?.minute]);
  
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
  
  // Create grid template
  const gridStyle = {
    gridTemplateColumns: `repeat(${game_map.width}, 30px)`,
    gridTemplateRows: `repeat(${game_map.height}, 30px)`
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
            if (agentsAtPosition.length > 0) {
              setSelectedAgent(agentsAtPosition[0].agent_id);
            }
          }}
          title={`(${x}, ${y}) - ${cellType}${itemsAtPosition.length > 0 ? ` - ${itemsAtPosition.length} items` : ''}`}
        >
          {/* Render items */}
          {itemsAtPosition.length > 0 && (
            <div style={{
              position: 'absolute',
              top: '2px',
              right: '2px',
              fontSize: '8px',
              color: '#fff',
              backgroundColor: 'rgba(0,0,0,0.7)',
              borderRadius: '2px',
              padding: '1px 2px',
              zIndex: 2
            }}>
              {itemsAtPosition.length}
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
                  zIndex: 10 + index,
                  fontSize: '7px',
                  fontWeight: 'bold'
                }}
                title={`${agent.name} (${agent.role})\nHP: ${agent.hp}, Sanity: ${agent.sanity}\nPosition: (${agent.position[0]}, ${agent.position[1]})`}
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
    <div className="map-container">
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h3 style={{ margin: 0 }}>
            🗺️ 监狱地图 ({game_map.width}x{game_map.height})
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
          
          {/* SVG overlay for trajectory lines */}
          {showTrajectories && (
            <svg
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: `${game_map.width * 31}px`, // 30px cell + 1px gap
                height: `${game_map.height * 31}px`,
                pointerEvents: 'none',
                zIndex: 5
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
                  const x = point.x * 31 + 15; // Cell center (30px + 1px gap)
                  const y = point.y * 31 + 15;
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
                      
                      const x = point.x * 31 + 15;
                      const y = point.y * 31 + 15;
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
                        cx={adjustedTrajectory[0].x * 31 + 15}
                        cy={adjustedTrajectory[0].y * 31 + 15}
                        r="3"
                        fill={pathColor}
                        opacity="0.8"
                        stroke="white"
                        strokeWidth="1"
                      />
                    )}
                    
                    {/* End point marker (current position) */}
                    <circle
                      cx={currentPos.x * 31 + 15}
                      cy={currentPos.y * 31 + 15}
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
          fontSize: '12px',
          color: '#ccc'
        }}>
          <div>
            <span style={{ color: '#4a4a4a', backgroundColor: '#4a4a4a', padding: '2px 4px', margin: '2px' }}>■</span> Cell Block
            <span style={{ color: '#8B4513', backgroundColor: '#8B4513', padding: '2px 4px', margin: '2px' }}>■</span> Cafeteria
            <span style={{ color: '#228B22', backgroundColor: '#228B22', padding: '2px 4px', margin: '2px' }}>■</span> Yard
            <span style={{ color: '#800000', backgroundColor: '#800000', padding: '2px 4px', margin: '2px' }}>■</span> Solitary
            <span style={{ color: '#000080', backgroundColor: '#000080', padding: '2px 4px', margin: '2px' }}>■</span> Guard Room
          </div>
          <div style={{ marginTop: '10px' }}>
            <span style={{ color: '#0066cc', backgroundColor: '#0066cc', padding: '2px 4px', margin: '2px', borderRadius: '50%' }}>G1</span> Guard
            <span style={{ color: '#cc6600', backgroundColor: '#cc6600', padding: '2px 4px', margin: '2px', borderRadius: '50%' }}>P1</span> Prisoner
            {showTrajectories && (
              <span style={{ color: '#888', fontSize: '10px', marginLeft: '10px' }}>
                ━━━ 移动轨迹 (虚线+箭头显示方向)
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default MapView;