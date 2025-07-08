/**
 * Agent Details component - Right bottom panel
 * Shows detailed agent information including thinking process and complete prompt
 */
import React, { useState, useEffect } from 'react';
import useWorldStore from '../store/worldStore';

function AgentDetails() {
  const { worldState, selectedAgent } = useWorldStore();
  const [detailView, setDetailView] = useState('thinking'); // 'thinking', 'prompt', 'memory', 'stats'
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

  // Load agent memory data when memory tab is selected
  useEffect(() => {
    if (!selectedAgent || !worldState?.session_id || detailView !== 'memory') {
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
        gap: '3px', 
        marginBottom: '15px',
        fontSize: '10px'
      }}>
        {[
          { key: 'thinking', label: '🧠 思考', icon: '🧠' },
          { key: 'prompt', label: '📝 提示词', icon: '📝' },
          { key: 'memory', label: '💭 记忆', icon: '💭' },
          { key: 'stats', label: '📊 详细状态', icon: '📊' }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setDetailView(tab.key)}
            style={{
              padding: '4px 8px',
              backgroundColor: detailView === tab.key ? '#007bff' : '#444',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              fontSize: '10px',
              cursor: 'pointer'
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
            <h3 style={{ fontSize: '12px', margin: '0 0 10px 0', color: '#4caf50' }}>🧠 最新思考过程</h3>
            {loadingPromptData ? (
              <div style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
                ⏳ 加载中...
              </div>
            ) : agentPromptData?.thinking_process ? (
              <div style={{ 
                whiteSpace: 'pre-wrap', 
                fontSize: '11px', 
                lineHeight: '1.4',
                color: '#ddd',
                fontFamily: 'monospace'
              }}>
                {agentPromptData.thinking_process}
              </div>
            ) : selectedAgentData.last_thinking ? (
              <div style={{ 
                whiteSpace: 'pre-wrap', 
                fontSize: '11px', 
                lineHeight: '1.4',
                color: '#ddd',
                fontFamily: 'monospace'
              }}>
                {selectedAgentData.last_thinking}
              </div>
            ) : (
              <div style={{ color: '#666', fontStyle: 'italic', textAlign: 'center', padding: '20px' }}>
                暂无思考记录
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
        )}
        
        {detailView === 'prompt' && (
          <div>
            <h3 style={{ fontSize: '12px', margin: '0 0 10px 0', color: '#ff9800' }}>📝 完整提示词</h3>
            {loadingPromptData ? (
              <div style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
                ⏳ 加载中...
              </div>
            ) : agentPromptData?.prompt_content ? (
              <div style={{ 
                whiteSpace: 'pre-wrap', 
                fontSize: '9px', 
                lineHeight: '1.3',
                color: '#ccc',
                fontFamily: 'monospace',
                backgroundColor: '#1a1a1a',
                padding: '8px',
                borderRadius: '3px',
                border: '1px solid #444'
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
                  fontSize: '10px', 
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
          </div>
        )}
        
        {detailView === 'memory' && (
          <div>
            <h3 style={{ fontSize: '12px', margin: '0 0 10px 0', color: '#6f42c1' }}>💭 记忆系统</h3>
            
            {loadingMemoryData ? (
              <div style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
                ⏳ 加载记忆数据中...
              </div>
            ) : agentMemoryData ? (
              <div>
                {/* Complete History with Timestamps */}
                {agentMemoryData.timestamped_history?.length > 0 && (
                  <div style={{ marginBottom: '15px' }}>
                    <h4 style={{ fontSize: '11px', margin: '0 0 5px 0', color: '#4caf50' }}>📚 完整历史记忆 (最新在上)</h4>
                    <div style={{ 
                      maxHeight: '250px', 
                      overflowY: 'auto',
                      fontSize: '9px',
                      backgroundColor: '#1a1a1a',
                      borderRadius: '3px',
                      border: '1px solid #444'
                    }}>
                      {agentMemoryData.timestamped_history.map((entry, index) => (
                        <div 
                          key={index}
                          style={{ 
                            padding: '6px 8px', 
                            margin: '0',
                            borderBottom: index < agentMemoryData.timestamped_history.length - 1 ? '1px solid #333' : 'none',
                            borderLeft: `3px solid ${
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
                            marginBottom: '2px',
                            fontWeight: 'bold'
                          }}>
                            🕒 {entry.timestamp}
                          </div>
                          <div style={{ color: '#ddd', lineHeight: '1.3' }}>
                            {entry.content}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Thinking History */}
                {agentMemoryData.thinking_history?.length > 0 && (
                  <div style={{ marginBottom: '15px' }}>
                    <h4 style={{ fontSize: '11px', margin: '0 0 5px 0', color: '#ff9800' }}>🧠 思考历史 (最近记录)</h4>
                    <div style={{ 
                      maxHeight: '120px', 
                      overflowY: 'auto',
                      fontSize: '9px',
                      backgroundColor: '#1a1a1a',
                      borderRadius: '3px',
                      border: '1px solid #444'
                    }}>
                      {agentMemoryData.thinking_history.slice(-5).reverse().map((thinking, index) => (
                        <div 
                          key={index}
                          style={{ 
                            padding: '6px 8px', 
                            margin: '0',
                            borderBottom: index < Math.min(agentMemoryData.thinking_history.length, 5) - 1 ? '1px solid #333' : 'none',
                            borderLeft: '3px solid #ff9800'
                          }}
                        >
                          <div style={{ color: '#ddd', lineHeight: '1.3', whiteSpace: 'pre-wrap' }}>
                            {thinking}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Short-term Memory */}
                {agentMemoryData.enhanced_memory?.short_term?.length > 0 && (
                  <div style={{ marginBottom: '15px' }}>
                    <h4 style={{ fontSize: '11px', margin: '0 0 5px 0', color: '#17a2b8' }}>🔄 短期记忆缓存</h4>
                    <div style={{ fontSize: '9px' }}>
                      {agentMemoryData.enhanced_memory.short_term.map((memory, index) => (
                        <div 
                          key={index}
                          style={{ 
                            padding: '4px 6px', 
                            margin: '2px 0',
                            backgroundColor: '#333',
                            borderRadius: '3px',
                            borderLeft: '3px solid #17a2b8',
                            fontSize: '9px'
                          }}
                        >
                          {memory}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: '#666', fontStyle: 'italic', textAlign: 'center', padding: '20px' }}>
                暂无记忆数据
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
      </div>
    </div>
  );
}

export default AgentDetails;