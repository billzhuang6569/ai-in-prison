/**
 * Agent Preview component - Left sidebar
 * Shows agent overview with recent actions and quick status
 */
import React, { useState, useEffect } from 'react';
import useWorldStore from '../store/worldStore';

function AgentPreview() {
  const { worldState, selectedAgent, setSelectedAgent } = useWorldStore();
  const [agentRecentActions, setAgentRecentActions] = useState({});
  
  // Load recent actions for each agent
  useEffect(() => {
    if (!worldState?.session_id) return;
    
    const loadRecentActions = async () => {
      try {
        const response = await fetch(`http://localhost:24861/api/v1/events?limit=100&session_id=${worldState.session_id}`);
        const data = await response.json();
        
        // Group recent actions by agent
        const actionsByAgent = {};
        data.events.forEach(event => {
          if (!actionsByAgent[event.agent_name]) {
            actionsByAgent[event.agent_name] = [];
          }
          actionsByAgent[event.agent_name].push({
            description: event.description,
            event_type: event.event_type,
            timestamp: event.timestamp,
            day: event.day,
            hour: event.hour,
            minute: event.minute
          });
        });
        
        // Keep only the 3 most recent actions per agent
        Object.keys(actionsByAgent).forEach(agentName => {
          actionsByAgent[agentName] = actionsByAgent[agentName]
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 3);
        });
        
        setAgentRecentActions(actionsByAgent);
      } catch (error) {
        console.error('Error loading recent actions:', error);
      }
    };
    
    loadRecentActions();
    
    // Refresh every 10 seconds when running
    const interval = worldState?.is_running ? setInterval(loadRecentActions, 10000) : null;
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [worldState?.session_id, worldState?.is_running]);
  
  const getAgentStatusColor = (agent) => {
    if (agent.hp <= 20) return '#f44336';
    if (agent.sanity <= 20) return '#ff9800';
    if (agent.hp <= 50 || agent.sanity <= 50) return '#ffeb3b';
    return '#4caf50';
  };
  
  const getActionTypeIcon = (type) => {
    const icons = {
      'rest': '😴',
      'move': '🚶',
      'speak': '💬',
      'attack': '⚔️',
      'use_item': '🔧',
      'system': '⚙️'
    };
    return icons[type] || '❓';
  };
  
  const handleAgentSelect = (agentId) => {
    setSelectedAgent(agentId === selectedAgent ? null : agentId);
  };
  
  if (!worldState?.agents) {
    return (
      <div className="panel">
        <h2>👥 智能体</h2>
        <div style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
          等待数据...
        </div>
      </div>
    );
  }
  
  const agents = Object.values(worldState.agents);
  
  return (
    <div className="panel" style={{ padding: '10px' }}>
      <h2 style={{ fontSize: '16px', margin: '0 0 15px 0' }}>👥 智能体</h2>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {agents.map(agent => (
          <div 
            key={agent.agent_id}
            onClick={() => handleAgentSelect(agent.agent_id)}
            style={{ 
              padding: '8px',
              backgroundColor: selectedAgent === agent.agent_id ? '#444' : '#333',
              borderRadius: '4px',
              cursor: 'pointer',
              border: selectedAgent === agent.agent_id ? '2px solid #007bff' : '1px solid #555',
              transition: 'all 0.2s ease'
            }}
          >
            {/* Agent Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
              <div style={{ fontWeight: 'bold', fontSize: '12px' }}>
                {agent.role === 'Guard' ? '👮' : '👤'} {agent.name}
              </div>
              <div 
                style={{ 
                  width: '8px', 
                  height: '8px', 
                  borderRadius: '50%', 
                  backgroundColor: getAgentStatusColor(agent)
                }}
                title={`HP: ${agent.hp}, Sanity: ${agent.sanity}`}
              />
            </div>
            
            {/* Status Bars */}
            <div style={{ marginBottom: '5px' }}>
              <div style={{ display: 'flex', gap: '3px', alignItems: 'center' }}>
                <span style={{ fontSize: '8px', color: '#ccc', width: '16px' }}>❤️</span>
                <div style={{ flex: 1, height: '4px', backgroundColor: '#555', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ 
                    width: `${agent.hp}%`, 
                    height: '100%', 
                    backgroundColor: '#f44336',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
                <span style={{ fontSize: '8px', color: '#ccc', minWidth: '20px' }}>{agent.hp}</span>
              </div>
              
              <div style={{ display: 'flex', gap: '3px', alignItems: 'center', marginTop: '2px' }}>
                <span style={{ fontSize: '8px', color: '#ccc', width: '16px' }}>🧠</span>
                <div style={{ flex: 1, height: '4px', backgroundColor: '#555', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ 
                    width: `${agent.sanity}%`, 
                    height: '100%', 
                    backgroundColor: '#6f42c1',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
                <span style={{ fontSize: '8px', color: '#ccc', minWidth: '20px' }}>{agent.sanity}</span>
              </div>
            </div>
            
            {/* Position */}
            <div style={{ fontSize: '9px', color: '#999', marginBottom: '5px' }}>
              📍 ({agent.position[0]}, {agent.position[1]})
            </div>
            
            {/* Recent Actions */}
            <div style={{ fontSize: '8px' }}>
              <div style={{ color: '#ccc', marginBottom: '3px' }}>最近动作:</div>
              {agentRecentActions[agent.name] && agentRecentActions[agent.name].length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
                  {agentRecentActions[agent.name].map((action, index) => (
                    <div 
                      key={index}
                      style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '3px',
                        padding: '1px 3px',
                        backgroundColor: '#444',
                        borderRadius: '2px'
                      }}
                    >
                      <span>{getActionTypeIcon(action.event_type)}</span>
                      <span style={{ 
                        flex: 1, 
                        overflow: 'hidden', 
                        textOverflow: 'ellipsis', 
                        whiteSpace: 'nowrap',
                        color: '#ddd'
                      }}>
                        {action.description.length > 20 
                          ? action.description.substring(0, 17) + '...'
                          : action.description
                        }
                      </span>
                      <span style={{ color: '#888', fontSize: '7px' }}>
                        {action.hour}:{action.minute.toString().padStart(2, '0')}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ color: '#666', fontStyle: 'italic' }}>无动作记录</div>
              )}
            </div>
            
            {/* Status Tags */}
            {agent.status_tags.length > 0 && (
              <div style={{ marginTop: '5px' }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2px' }}>
                  {agent.status_tags.slice(0, 2).map(tag => (
                    <span 
                      key={tag} 
                      style={{
                        backgroundColor: '#666',
                        color: '#fff',
                        padding: '1px 3px',
                        borderRadius: '2px',
                        fontSize: '7px'
                      }}
                    >
                      {tag}
                    </span>
                  ))}
                  {agent.status_tags.length > 2 && (
                    <span style={{ fontSize: '7px', color: '#888' }}>
                      +{agent.status_tags.length - 2}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Selection Helper */}
      <div style={{ 
        marginTop: '10px', 
        padding: '5px', 
        backgroundColor: '#444', 
        borderRadius: '3px',
        fontSize: '9px',
        color: '#ccc',
        textAlign: 'center'
      }}>
        {selectedAgent ? '点击取消选择' : '点击选择智能体'}
      </div>
    </div>
  );
}

export default AgentPreview;