/**
 * Agent Cards component - Right top panel
 * Shows agent cards with health, personality, relationships, and inventory
 */
import React, { useState } from 'react';
import useWorldStore from '../store/worldStore';

function AgentCards() {
  const { worldState, selectedAgent, setSelectedAgent } = useWorldStore();
  const [cardView, setCardView] = useState('status'); // 'status' (合并了HP、关系值、道具)
  
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
  
  const handleCardClick = async (agentId) => {
    setSelectedAgent(agentId);
    
    // Call refresh API to get latest agent data
    try {
      const response = await fetch(`http://localhost:24861/api/v1/agents/${agentId}/refresh`);
      if (response.ok) {
        const refreshedData = await response.json();
        // The data will be automatically updated via WebSocket, but we can trigger a store update if needed
        console.log('Agent data refreshed:', refreshedData.agent.name);
      }
    } catch (error) {
      console.error('Failed to refresh agent data:', error);
    }
  };
  
  return (
    <div className="panel">
      <h2>🎴 智能体卡片</h2>
      
      {/* View Toggle - 简化为一个合并标签页 */}
      <div style={{ 
        display: 'flex', 
        gap: '3px', 
        marginBottom: '15px',
        fontSize: '10px',
        justifyContent: 'center'
      }}>
        <button
          onClick={() => setCardView('status')}
          style={{
            padding: '6px 12px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '11px',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          📊 状态总览
        </button>
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
            
            {/* 合并的状态总览 - 包含HP、关系值、道具 */}
            <div>
              {/* Health Status */}
              <div style={{ marginBottom: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                  <span style={{ fontSize: '9px', color: '#ccc', fontWeight: 'bold' }}>❤️ HP</span>
                  <span style={{ fontSize: '9px' }}>{agent.hp}</span>
                </div>
                <div style={{ height: '4px', backgroundColor: '#555', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ 
                    width: `${agent.hp}%`, 
                    height: '100%', 
                    backgroundColor: agent.hp > 70 ? '#4caf50' : agent.hp > 30 ? '#ff9800' : '#f44336',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>
              
              <div style={{ marginBottom: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                  <span style={{ fontSize: '9px', color: '#ccc', fontWeight: 'bold' }}>🧠 理智</span>
                  <span style={{ fontSize: '9px' }}>{agent.sanity}</span>
                </div>
                <div style={{ height: '4px', backgroundColor: '#555', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ 
                    width: `${agent.sanity}%`, 
                    height: '100%', 
                    backgroundColor: agent.sanity > 70 ? '#6f42c1' : agent.sanity > 30 ? '#e83e8c' : '#dc3545',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>
              
              {/* Key Relationships */}
              <div style={{ marginBottom: '8px' }}>
                <div style={{ fontSize: '9px', color: '#ccc', fontWeight: 'bold', marginBottom: '4px' }}>
                  🤝 关系值
                </div>
                {Object.entries(agent.relationships || {}).length > 0 ? (
                  Object.entries(agent.relationships).slice(0, 2).map(([targetName, relationship]) => (
                    <div key={targetName} style={{ marginBottom: '3px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '8px', color: '#ccc' }}>{targetName}</span>
                        <span 
                          style={{ 
                            fontSize: '8px',
                            color: getRelationshipColor(relationship.score),
                            fontWeight: 'bold'
                          }}
                        >
                          {relationship.score}
                        </span>
                      </div>
                      <div style={{ height: '2px', backgroundColor: '#555', borderRadius: '1px', overflow: 'hidden' }}>
                        <div style={{ 
                          width: `${relationship.score}%`, 
                          height: '100%', 
                          backgroundColor: getRelationshipColor(relationship.score),
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: '8px', color: '#666', textAlign: 'center', padding: '4px' }}>
                    暂无关系数据
                  </div>
                )}
              </div>
              
              {/* Inventory */}
              <div style={{ marginBottom: '8px' }}>
                <div style={{ fontSize: '9px', color: '#ccc', fontWeight: 'bold', marginBottom: '4px' }}>
                  🎒 道具
                </div>
                {agent.inventory && agent.inventory.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2px' }}>
                    {agent.inventory.slice(0, 4).map((item, index) => (
                      <div 
                        key={index}
                        style={{
                          backgroundColor: '#666',
                          color: '#fff',
                          padding: '2px 4px',
                          borderRadius: '3px',
                          fontSize: '7px',
                          textAlign: 'center',
                          border: '1px solid #777'
                        }}
                        title={item.description || item.name}
                      >
                        {item.name}
                      </div>
                    ))}
                    {agent.inventory.length > 4 && (
                      <div style={{ fontSize: '7px', color: '#888', padding: '2px' }}>
                        +{agent.inventory.length - 4}
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ fontSize: '8px', color: '#666', textAlign: 'center', padding: '4px' }}>
                    无物品
                  </div>
                )}
              </div>
              
              {/* Position and Actions */}
              <div style={{ fontSize: '8px', color: '#999', marginTop: '6px', textAlign: 'center' }}>
                📍 ({agent.position[0]}, {agent.position[1]}) | ⚡ {agent.action_points}/3
              </div>
            </div>
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