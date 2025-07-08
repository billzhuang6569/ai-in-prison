/**
 * Agent Cards component - Right top panel
 * Shows agent cards with health, personality, relationships, and inventory
 */
import React, { useState } from 'react';
import useWorldStore from '../store/worldStore';

function AgentCards() {
  const { worldState, selectedAgent, setSelectedAgent } = useWorldStore();
  const [cardView, setCardView] = useState('overview'); // 'overview', 'personality', 'relationships', 'inventory'
  
  if (!worldState?.agents) {
    return (
      <div className="panel">
        <h2>🎴 智能体卡片</h2>
        <div style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
          等待数据...
        </div>
      </div>
    );
  }
  
  const agents = Object.values(worldState.agents);
  
  const getPersonalityIcon = (trait, value) => {
    const icons = {
      aggression: value > 70 ? '😡' : value > 30 ? '😐' : '😇',
      empathy: value > 70 ? '❤️' : value > 30 ? '💛' : '🖤',
      logic: value > 70 ? '🧠' : value > 30 ? '🤔' : '😵',
      obedience: value > 70 ? '🤝' : value > 30 ? '😑' : '🙄',
      resilience: value > 70 ? '💪' : value > 30 ? '😌' : '😰'
    };
    return icons[trait] || '❓';
  };
  
  const getRelationshipColor = (score) => {
    if (score > 70) return '#4caf50';
    if (score > 40) return '#ffeb3b';
    if (score > 20) return '#ff9800';
    return '#f44336';
  };
  
  const handleCardClick = (agentId) => {
    setSelectedAgent(agentId);
  };
  
  return (
    <div className="panel">
      <h2>🎴 智能体卡片</h2>
      
      {/* View Toggle */}
      <div style={{ 
        display: 'flex', 
        gap: '3px', 
        marginBottom: '15px',
        fontSize: '10px'
      }}>
        {[
          { key: 'overview', label: '📊 概览', icon: '📊' },
          { key: 'personality', label: '🧭 性格', icon: '🧭' },
          { key: 'relationships', label: '🤝 关系', icon: '🤝' },
          { key: 'inventory', label: '🎒 物品', icon: '🎒' }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setCardView(tab.key)}
            style={{
              padding: '4px 6px',
              backgroundColor: cardView === tab.key ? '#007bff' : '#444',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              fontSize: '9px',
              cursor: 'pointer'
            }}
          >
            {tab.icon}
          </button>
        ))}
      </div>
      
      {/* Agent Cards */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
        gap: '8px',
        maxHeight: '400px',
        overflowY: 'auto'
      }}>
        {agents.map(agent => (
          <div 
            key={agent.agent_id}
            onClick={() => handleCardClick(agent.agent_id)}
            style={{ 
              padding: '8px',
              backgroundColor: selectedAgent === agent.agent_id ? '#444' : '#333',
              borderRadius: '6px',
              cursor: 'pointer',
              border: selectedAgent === agent.agent_id ? '2px solid #007bff' : '1px solid #555',
              transition: 'all 0.2s ease',
              fontSize: '10px'
            }}
          >
            {/* Agent Header */}
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              marginBottom: '8px' 
            }}>
              <div style={{ fontWeight: 'bold', fontSize: '11px' }}>
                {agent.role === 'Guard' ? '👮' : '👤'} {agent.name}
              </div>
              <div style={{ fontSize: '8px', color: '#888' }}>
                {agent.role === 'Guard' ? 'G' : 'P'}{agents.indexOf(agent) + 1}
              </div>
            </div>
            
            {/* Card Content based on view */}
            {cardView === 'overview' && (
              <div>
                {/* Health Status */}
                <div style={{ marginBottom: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                    <span style={{ fontSize: '8px', color: '#ccc' }}>❤️ HP</span>
                    <span style={{ fontSize: '8px' }}>{agent.hp}</span>
                  </div>
                  <div style={{ height: '3px', backgroundColor: '#555', borderRadius: '2px', overflow: 'hidden' }}>
                    <div style={{ 
                      width: `${agent.hp}%`, 
                      height: '100%', 
                      backgroundColor: '#f44336'
                    }} />
                  </div>
                </div>
                
                <div style={{ marginBottom: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                    <span style={{ fontSize: '8px', color: '#ccc' }}>🧠 理智</span>
                    <span style={{ fontSize: '8px' }}>{agent.sanity}</span>
                  </div>
                  <div style={{ height: '3px', backgroundColor: '#555', borderRadius: '2px', overflow: 'hidden' }}>
                    <div style={{ 
                      width: `${agent.sanity}%`, 
                      height: '100%', 
                      backgroundColor: '#6f42c1'
                    }} />
                  </div>
                </div>
                
                {/* Position and Actions */}
                <div style={{ fontSize: '8px', color: '#999', marginBottom: '4px' }}>
                  📍 ({agent.position[0]}, {agent.position[1]}) | ⚡ {agent.action_points}/3
                </div>
                
                {/* Status Tags */}
                {agent.status_tags.length > 0 && (
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
                      <span style={{ fontSize: '7px', color: '#888' }}>+{agent.status_tags.length - 2}</span>
                    )}
                  </div>
                )}
              </div>
            )}
            
            {cardView === 'personality' && (
              <div>
                {Object.entries(agent.traits).map(([trait, value]) => (
                  <div key={trait} style={{ marginBottom: '4px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1px' }}>
                      <span style={{ fontSize: '8px', color: '#ccc' }}>
                        {getPersonalityIcon(trait, value)} {trait}
                      </span>
                      <span style={{ fontSize: '8px' }}>{value}</span>
                    </div>
                    <div style={{ height: '2px', backgroundColor: '#555', borderRadius: '1px', overflow: 'hidden' }}>
                      <div style={{ 
                        width: `${value}%`, 
                        height: '100%', 
                        backgroundColor: value > 50 ? '#4caf50' : '#ff9800'
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {cardView === 'relationships' && (
              <div>
                {Object.entries(agent.relationships || {}).length > 0 ? (
                  Object.entries(agent.relationships).slice(0, 4).map(([targetName, relationship]) => (
                    <div key={targetName} style={{ marginBottom: '3px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '8px', color: '#ccc' }}>{targetName}</span>
                        <span 
                          style={{ 
                            fontSize: '8px',
                            color: getRelationshipColor(relationship.score)
                          }}
                        >
                          {relationship.score}
                        </span>
                      </div>
                      <div style={{ height: '2px', backgroundColor: '#555', borderRadius: '1px', overflow: 'hidden' }}>
                        <div style={{ 
                          width: `${relationship.score}%`, 
                          height: '100%', 
                          backgroundColor: getRelationshipColor(relationship.score)
                        }} />
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: '8px', color: '#666', textAlign: 'center', padding: '10px' }}>
                    暂无关系数据
                  </div>
                )}
              </div>
            )}
            
            {cardView === 'inventory' && (
              <div>
                {agent.inventory && agent.inventory.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
                    {agent.inventory.slice(0, 6).map((item, index) => (
                      <div 
                        key={index}
                        style={{
                          backgroundColor: '#666',
                          color: '#fff',
                          padding: '2px 4px',
                          borderRadius: '3px',
                          fontSize: '7px',
                          textAlign: 'center'
                        }}
                        title={item.description || item.name}
                      >
                        🎒 {item.name}
                      </div>
                    ))}
                    {agent.inventory.length > 6 && (
                      <div style={{ fontSize: '7px', color: '#888' }}>
                        +{agent.inventory.length - 6}
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ fontSize: '8px', color: '#666', textAlign: 'center', padding: '10px' }}>
                    🎒 无物品
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Selection Info */}
      <div style={{ 
        marginTop: '10px', 
        padding: '5px', 
        backgroundColor: '#444', 
        borderRadius: '3px',
        fontSize: '9px',
        color: '#ccc',
        textAlign: 'center'
      }}>
        {selectedAgent ? `已选择: ${agents.find(a => a.agent_id === selectedAgent)?.name}` : '点击卡片查看详情'}
      </div>
    </div>
  );
}

export default AgentCards;