/**
 * Agent Details component - Right bottom panel
 * Shows detailed agent information including thinking process and complete prompt
 */
import React, { useState, useEffect } from 'react';
import useWorldStore from '../store/worldStore';

function AgentDetails() {
  const { worldState, selectedAgent } = useWorldStore();
  const [detailView, setDetailView] = useState('thinking'); // 'thinking', 'history', 'thoughts', 'shortterm', 'stats'
  const [agentPromptData, setAgentPromptData] = useState(null);
  const [loadingPromptData, setLoadingPromptData] = useState(false);
  const [agentMemoryData, setAgentMemoryData] = useState(null);
  const [loadingMemoryData, setLoadingMemoryData] = useState(false);
  
  const selectedAgentData = selectedAgent ? worldState?.agents[selectedAgent] : null;
  
  // Load agent prompt and thinking data
  useEffect(() => {
    if (!selectedAgent || !worldState?.session_id) {
      setAgentPromptData(null);
      return;
    }
    
    const loadPromptData = async () => {
      setLoadingPromptData(true);
      try {
        // Get prompt data from the worldState first (most recent)
        if (worldState.agent_prompts && worldState.agent_prompts[selectedAgent]) {
          setAgentPromptData(worldState.agent_prompts[selectedAgent]);
        } else {
          // Fallback: fetch from API if not in worldState
          const response = await fetch(`http://localhost:24861/api/v1/agents/${selectedAgent}/prompt-history?limit=1`);
          if (response.ok) {
            const data = await response.json();
            if (data.length > 0) {
              setAgentPromptData(data[0]);
            }
          }
        }
      } catch (error) {
        console.error('Error loading prompt data:', error);
      } finally {
        setLoadingPromptData(false);
      }
    };
    
    loadPromptData();
  }, [selectedAgent, worldState?.session_id, worldState?.agent_prompts]);

  // Load agent memory data when memory-related tabs are selected
  useEffect(() => {
    if (!selectedAgent || !worldState?.session_id || !['history', 'thoughts', 'shortterm'].includes(detailView)) {
      return;
    }
    
    const loadMemoryData = async () => {
      setLoadingMemoryData(true);
      try {
        const response = await fetch(`http://localhost:24861/api/v1/agents/${selectedAgent}/memory`);
        if (response.ok) {
          const memoryData = await response.json();
          setAgentMemoryData(memoryData);
        }
      } catch (error) {
        console.error('Error loading memory data:', error);
      } finally {
        setLoadingMemoryData(false);
      }
    };
    
    loadMemoryData();
  }, [selectedAgent, worldState?.session_id, detailView]);
  
  if (!selectedAgent || !selectedAgentData) {
    return (
      <div className="panel">
        <h2>🔍 智能体详情</h2>
        <div style={{ 
          color: '#666', 
          textAlign: 'center', 
          padding: '40px 20px',
          fontSize: '14px'
        }}>
          <div style={{ fontSize: '40px', marginBottom: '10px' }}>👆</div>
          请在左侧或右上角选择一个智能体
        </div>
      </div>
    );
  }
  
  return (
    <div className="panel">
      <h2>🔍 {selectedAgentData.name} 详情</h2>
      
      {/* Detail View Tabs */}
      <div style={{ 
        display: 'flex', 
        gap: '2px', 
        marginBottom: '15px',
        fontSize: '9px',
        flexWrap: 'wrap'
      }}>
        {[
          { key: 'thinking', label: '🧠 思考+提示词', icon: '🧠' },
          { key: 'history', label: '📚 历史记忆', icon: '📚' },
          { key: 'thoughts', label: '💭 思考历史', icon: '💭' },
          { key: 'shortterm', label: '🔄 短期缓存', icon: '🔄' },
          { key: 'stats', label: '📊 详细状态', icon: '📊' },
          { key: 'inventory', label: '🎒 道具清单', icon: '🎒' }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setDetailView(tab.key)}
            style={{
              padding: '3px 6px',
              backgroundColor: detailView === tab.key ? '#007bff' : '#444',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              fontSize: '9px',
              cursor: 'pointer',
              flex: '1',
              minWidth: '60px'
            }}
          >
            {tab.icon}
          </button>
        ))}
      </div>
      
      {/* Detail Content */}
      <div style={{ 
        maxHeight: '350px', 
        overflowY: 'auto',
        backgroundColor: '#222',
        borderRadius: '4px',
        padding: '10px'
      }}>
        {detailView === 'thinking' && (
          <div>
            {/* 思考过程部分 */}
            <div style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '12px', margin: '0 0 10px 0', color: '#4caf50' }}>🧠 最新思考过程</h3>
              {loadingPromptData ? (
                <div style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
                  ⏳ 加载中...
                </div>
              ) : agentPromptData?.thinking_process ? (
                <div style={{ 
                  whiteSpace: 'pre-wrap', 
                  fontSize: '10px', 
                  lineHeight: '1.4',
                  color: '#ddd',
                  fontFamily: 'monospace',
                  backgroundColor: '#1a1a1a',
                  padding: '8px',
                  borderRadius: '3px',
                  border: '1px solid #444',
                  marginBottom: '10px'
                }}>
                  {agentPromptData.thinking_process}
                </div>
              ) : selectedAgentData.last_thinking ? (
                <div style={{ 
                  whiteSpace: 'pre-wrap', 
                  fontSize: '10px', 
                  lineHeight: '1.4',
                  color: '#ddd',
                  fontFamily: 'monospace',
                  backgroundColor: '#1a1a1a',
                  padding: '8px',
                  borderRadius: '3px',
                  border: '1px solid #444',
                  marginBottom: '10px'
                }}>
                  {selectedAgentData.last_thinking}
                </div>
              ) : (
                <div style={{ color: '#666', fontStyle: 'italic', textAlign: 'center', padding: '20px' }}>
                  暂无思考记录
                </div>
              )}
            </div>
            
            {/* 完整提示词部分 */}
            <div>
              <h3 style={{ fontSize: '12px', margin: '0 0 10px 0', color: '#ff9800' }}>📝 完整提示词</h3>
              {loadingPromptData ? (
                <div style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
                  ⏳ 加载中...
                </div>
              ) : agentPromptData?.prompt_content ? (
                <div style={{ 
                  whiteSpace: 'pre-wrap', 
                  fontSize: '8px', 
                  lineHeight: '1.3',
                  color: '#ccc',
                  fontFamily: 'monospace',
                  backgroundColor: '#1a1a1a',
                  padding: '8px',
                  borderRadius: '3px',
                  border: '1px solid #444',
                  maxHeight: '200px',
                  overflowY: 'auto'
                }}>
                  {agentPromptData.prompt_content}
                </div>
              ) : (
                <div style={{ color: '#666', fontStyle: 'italic', textAlign: 'center', padding: '20px' }}>
                  暂无提示词记录
                </div>
              )}
              
              {agentPromptData?.decision && (
                <div style={{ marginTop: '10px' }}>
                  <h4 style={{ fontSize: '11px', margin: '0 0 5px 0', color: '#4caf50' }}>🎯 AI决策结果:</h4>
                  <div style={{ 
                    fontSize: '9px', 
                    color: '#ddd',
                    backgroundColor: '#1a1a1a',
                    padding: '6px',
                    borderRadius: '3px',
                    border: '1px solid #444'
                  }}>
                    {agentPromptData.decision}
                  </div>
                </div>
              )}
              
              {agentPromptData?.timestamp && (
                <div style={{ 
                  marginTop: '10px', 
                  fontSize: '9px', 
                  color: '#888',
                  borderTop: '1px solid #444',
                  paddingTop: '8px'
                }}>
                  更新时间: {agentPromptData.timestamp}
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* 历史记忆标签页 */}
        {detailView === 'history' && (
          <div>
            <h3 style={{ fontSize: '12px', margin: '0 0 10px 0', color: '#4caf50' }}>📚 完整历史记忆</h3>
            
            {loadingMemoryData ? (
              <div style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
                ⏳ 加载记忆数据中...
              </div>
            ) : agentMemoryData?.timestamped_history?.length > 0 ? (
              <div style={{ 
                maxHeight: '320px', 
                overflowY: 'auto',
                fontSize: '9px'
              }}>
                {agentMemoryData.timestamped_history.map((entry, index) => (
                  <div 
                    key={index}
                    style={{ 
                      padding: '8px 10px', 
                      margin: '0 0 8px 0',
                      backgroundColor: '#1a1a1a',
                      borderRadius: '4px',
                      border: '1px solid #444',
                      borderLeft: `4px solid ${
                        entry.event_type === 'combat' ? '#f44336' :
                        entry.event_type === 'speech' ? '#2196f3' :
                        entry.event_type === 'movement' ? '#4caf50' :
                        '#6f42c1'
                      }`
                    }}
                  >
                    <div style={{ 
                      color: '#888', 
                      fontSize: '8px', 
                      marginBottom: '4px',
                      fontWeight: 'bold'
                    }}>
                      🕒 {entry.timestamp}
                    </div>
                    <div style={{ color: '#ddd', lineHeight: '1.4' }}>
                      {entry.content}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: '#666', fontStyle: 'italic', textAlign: 'center', padding: '20px' }}>
                暂无历史记忆数据
              </div>
            )}
          </div>
        )}
        
        {/* 思考历史标签页 */}
        {detailView === 'thoughts' && (
          <div>
            <h3 style={{ fontSize: '12px', margin: '0 0 10px 0', color: '#ff9800' }}>💭 思考历史</h3>
            
            {loadingMemoryData ? (
              <div style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
                ⏳ 加载记忆数据中...
              </div>
            ) : agentMemoryData?.thinking_history?.length > 0 ? (
              <div style={{ 
                maxHeight: '320px', 
                overflowY: 'auto',
                fontSize: '9px'
              }}>
                {agentMemoryData.thinking_history.slice(-10).reverse().map((thinking, index) => (
                  <div 
                    key={index}
                    style={{ 
                      padding: '8px 10px', 
                      margin: '0 0 8px 0',
                      backgroundColor: '#1a1a1a',
                      borderRadius: '4px',
                      border: '1px solid #444',
                      borderLeft: '4px solid #ff9800'
                    }}
                  >
                    <div style={{ color: '#ddd', lineHeight: '1.4', whiteSpace: 'pre-wrap' }}>
                      {thinking}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: '#666', fontStyle: 'italic', textAlign: 'center', padding: '20px' }}>
                暂无思考历史数据
              </div>
            )}
          </div>
        )}
        
        {/* 短期记忆缓存标签页 */}
        {detailView === 'shortterm' && (
          <div>
            <h3 style={{ fontSize: '12px', margin: '0 0 10px 0', color: '#17a2b8' }}>🔄 短期记忆缓存</h3>
            
            {loadingMemoryData ? (
              <div style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
                ⏳ 加载记忆数据中...
              </div>
            ) : agentMemoryData?.enhanced_memory?.short_term?.length > 0 ? (
              <div style={{ 
                maxHeight: '320px', 
                overflowY: 'auto',
                fontSize: '9px'
              }}>
                {agentMemoryData.enhanced_memory.short_term.map((memory, index) => (
                  <div 
                    key={index}
                    style={{ 
                      padding: '8px 10px', 
                      margin: '0 0 8px 0',
                      backgroundColor: '#1a1a1a',
                      borderRadius: '4px',
                      border: '1px solid #444',
                      borderLeft: '4px solid #17a2b8'
                    }}
                  >
                    <div style={{ color: '#ddd', lineHeight: '1.4' }}>
                      {memory}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: '#666', fontStyle: 'italic', textAlign: 'center', padding: '20px' }}>
                暂无短期记忆数据
              </div>
            )}
          </div>
        )}
        
        {detailView === 'stats' && (
          <div>
            <h3 style={{ fontSize: '12px', margin: '0 0 10px 0', color: '#e91e63' }}>📊 详细状态</h3>
            
            {/* Status Values */}
            <div style={{ marginBottom: '15px' }}>
              <h4 style={{ fontSize: '11px', margin: '0 0 8px 0', color: '#ccc' }}>🎯 状态值</h4>
              {[
                { key: 'hp', label: '生命值', icon: '❤️', color: '#f44336' },
                { key: 'sanity', label: '理智值', icon: '🧠', color: '#6f42c1' },
                { key: 'hunger', label: '饥饿值', icon: '🍽️', color: '#fd7e14' },
                { key: 'thirst', label: '口渴值', icon: '💧', color: '#17a2b8' },
                { key: 'strength', label: '体力值', icon: '💪', color: '#28a745' }
              ].map(stat => (
                <div key={stat.key} style={{ display: 'flex', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ width: '50px', fontSize: '10px', color: '#ccc' }}>
                    {stat.icon} {stat.label}
                  </span>
                  <div style={{ flex: 1, height: '12px', backgroundColor: '#555', borderRadius: '6px', overflow: 'hidden', margin: '0 8px' }}>
                    <div style={{ 
                      width: `${selectedAgentData[stat.key]}%`, 
                      height: '100%', 
                      backgroundColor: stat.color,
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                  <span style={{ fontSize: '11px', minWidth: '30px', textAlign: 'right' }}>
                    {selectedAgentData[stat.key]}/100
                  </span>
                </div>
              ))}
              
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ width: '50px', fontSize: '10px', color: '#ccc' }}>
                  ⚡ 行动点
                </span>
                <div style={{ flex: 1, margin: '0 8px' }}>
                  <div style={{ display: 'flex', gap: '2px' }}>
                    {[1, 2, 3].map(point => (
                      <div 
                        key={point}
                        style={{
                          width: '20px',
                          height: '12px',
                          backgroundColor: point <= selectedAgentData.action_points ? '#ffc107' : '#555',
                          borderRadius: '2px'
                        }}
                      />
                    ))}
                  </div>
                </div>
                <span style={{ fontSize: '11px', minWidth: '30px', textAlign: 'right' }}>
                  {selectedAgentData.action_points}/3
                </span>
              </div>
            </div>
            
            {/* Personality Traits */}
            <div style={{ marginBottom: '15px' }}>
              <h4 style={{ fontSize: '11px', margin: '0 0 8px 0', color: '#ccc' }}>🧭 性格特质</h4>
              {Object.entries(selectedAgentData.traits).map(([trait, value]) => (
                <div key={trait} style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ width: '60px', fontSize: '9px', color: '#ccc', textTransform: 'capitalize' }}>
                    {trait}
                  </span>
                  <div style={{ flex: 1, height: '8px', backgroundColor: '#555', borderRadius: '4px', overflow: 'hidden', margin: '0 8px' }}>
                    <div style={{ 
                      width: `${value}%`, 
                      height: '100%', 
                      backgroundColor: value > 50 ? '#4caf50' : '#ff9800'
                    }} />
                  </div>
                  <span style={{ fontSize: '9px', minWidth: '25px', textAlign: 'right' }}>
                    {value}
                  </span>
                </div>
              ))}
            </div>
            
            {/* Position and Role */}
            <div style={{ marginBottom: '15px' }}>
              <h4 style={{ fontSize: '11px', margin: '0 0 8px 0', color: '#ccc' }}>📍 位置信息</h4>
              <div style={{ fontSize: '10px', color: '#ddd' }}>
                <div>🏢 角色: {selectedAgentData.role === 'Guard' ? '狱警' : '囚犯'}</div>
                <div>📍 坐标: ({selectedAgentData.position[0]}, {selectedAgentData.position[1]})</div>
                <div>🆔 ID: {selectedAgentData.agent_id}</div>
              </div>
            </div>
            
            {/* Goals and Objectives */}
            {selectedAgentData.dynamic_goals?.current_goal && (
              <div>
                <h4 style={{ fontSize: '11px', margin: '0 0 8px 0', color: '#ccc' }}>🎯 当前目标</h4>
                <div style={{ 
                  fontSize: '10px', 
                  color: '#ddd',
                  backgroundColor: '#2a2a2a',
                  padding: '6px',
                  borderRadius: '3px'
                }}>
                  {selectedAgentData.dynamic_goals.current_goal}
                </div>
              </div>
            )}
          </div>
        )}

        {detailView === 'inventory' && (
          <div>
            <h3 style={{ fontSize: '12px', margin: '0 0 10px 0', color: '#4caf50' }}>🎒 完整道具清单</h3>
            
            {selectedAgentData.inventory && selectedAgentData.inventory.length > 0 ? (
              <div>
                <div style={{ 
                  marginBottom: '10px', 
                  fontSize: '10px', 
                  color: '#888',
                  backgroundColor: '#2a2a2a',
                  padding: '5px 8px',
                  borderRadius: '3px'
                }}>
                  📦 总计 {selectedAgentData.inventory.length} 件道具
                </div>
                
                <div style={{ display: 'grid', gap: '8px' }}>
                  {selectedAgentData.inventory.map((item, index) => (
                    <div 
                      key={`${item.item_id}-${index}`}
                      style={{
                        backgroundColor: '#1a1a1a',
                        border: '1px solid #444',
                        borderRadius: '4px',
                        padding: '8px',
                        transition: 'border-color 0.2s ease'
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.borderColor = '#666';
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.borderColor = '#444';
                      }}
                    >
                      {/* 道具头部信息 */}
                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center',
                        marginBottom: '4px'
                      }}>
                        <div style={{ 
                          fontSize: '11px', 
                          fontWeight: 'bold', 
                          color: '#fff'
                        }}>
                          📦 {item.name || '未知道具'}
                        </div>
                        <div style={{ 
                          fontSize: '8px', 
                          color: '#888',
                          backgroundColor: '#333',
                          padding: '1px 4px',
                          borderRadius: '2px'
                        }}>
                          {item.item_type || 'unknown'}
                        </div>
                      </div>
                      
                      {/* 道具描述 */}
                      {item.description && (
                        <div style={{
                          fontSize: '9px',
                          color: '#ccc',
                          lineHeight: '1.3',
                          marginBottom: '4px'
                        }}>
                          {item.description}
                        </div>
                      )}
                      
                      {/* 道具ID */}
                      <div style={{
                        fontSize: '8px',
                        color: '#666',
                        fontFamily: 'monospace'
                      }}>
                        ID: {item.item_id}
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* 道具统计信息 */}
                <div style={{ 
                  marginTop: '15px',
                  fontSize: '10px',
                  color: '#888'
                }}>
                  <h4 style={{ fontSize: '10px', margin: '0 0 5px 0', color: '#ccc' }}>📊 道具统计</h4>
                  {(() => {
                    const itemTypes = {};
                    selectedAgentData.inventory.forEach(item => {
                      const type = item.item_type || 'unknown';
                      itemTypes[type] = (itemTypes[type] || 0) + 1;
                    });
                    
                    return Object.entries(itemTypes).map(([type, count]) => (
                      <div key={type} style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between',
                        marginBottom: '2px',
                        padding: '2px 0'
                      }}>
                        <span>{type}:</span>
                        <span style={{ color: '#4caf50', fontWeight: 'bold' }}>{count} 件</span>
                      </div>
                    ));
                  })()}
                </div>
              </div>
            ) : (
              <div style={{ 
                color: '#666', 
                fontStyle: 'italic', 
                textAlign: 'center', 
                padding: '40px 20px',
                backgroundColor: '#1a1a1a',
                borderRadius: '4px',
                border: '1px dashed #444'
              }}>
                <div style={{ fontSize: '24px', marginBottom: '8px' }}>📭</div>
                <div style={{ fontSize: '11px' }}>该智能体暂无道具</div>
                <div style={{ fontSize: '9px', color: '#555', marginTop: '4px' }}>
                  道具会在游戏进行中获得
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default AgentDetails;