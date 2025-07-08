/**
 * Detail panel for selected agent information
 */
import React, { useState } from 'react';
import useWorldStore from '../store/worldStore';

function DetailPanel() {
  const { selectedAgent, worldState } = useWorldStore();
  const [showGoalInjection, setShowGoalInjection] = useState(false);
  const [goalName, setGoalName] = useState('');
  const [goalDescription, setGoalDescription] = useState('');
  const [goalPriority, setGoalPriority] = useState(5);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [customGoals, setCustomGoals] = useState('');
  const [showCustomGoals, setShowCustomGoals] = useState(false);
  const [environmentalContext, setEnvironmentalContext] = useState('');
  const [showEnvironmental, setShowEnvironmental] = useState(false);
  
  // Goal injection functions
  const handleInjectGoal = async () => {
    if (!goalName.trim() || !goalDescription.trim()) {
      alert('请填写目标名称和描述');
      return;
    }
    
    setIsSubmitting(true);
    try {
      const response = await fetch(`http://localhost:24861/api/v1/agents/${selectedAgent.agent_id}/inject_goal`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_id: selectedAgent.agent_id,
          goal_name: goalName,
          goal_description: goalDescription,
          priority: goalPriority
        })
      });
      
      if (response.ok) {
        alert('目标注入成功！');
        setGoalName('');
        setGoalDescription('');
        setGoalPriority(5);
        setShowGoalInjection(false);
      } else {
        const error = await response.json();
        alert(`注入失败: ${error.detail || '未知错误'}`);
      }
    } catch (error) {
      console.error('Goal injection error:', error);
      alert('网络错误，请重试');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handleClearGoals = async () => {
    if (!window.confirm('确定要清除所有手动目标吗？')) {
      return;
    }
    
    setIsSubmitting(true);
    try {
      const response = await fetch(`http://localhost:24861/api/v1/agents/${selectedAgent.agent_id}/clear_manual_goals`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        alert('手动目标已清除！');
      } else {
        const error = await response.json();
        alert(`清除失败: ${error.detail || '未知错误'}`);
      }
    } catch (error) {
      console.error('Clear goals error:', error);
      alert('网络错误，请重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSetCustomGoals = async () => {
    if (!customGoals.trim()) {
      alert('请输入自定义目标');
      return;
    }
    
    setIsSubmitting(true);
    try {
      const response = await fetch(`http://localhost:24861/api/v1/agents/${selectedAgent.agent_id}/custom_goals`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_id: selectedAgent.agent_id,
          custom_goals: customGoals
        })
      });
      
      if (response.ok) {
        alert('自定义目标设置成功！');
        setShowCustomGoals(false);
      } else {
        const error = await response.json();
        alert(`设置失败: ${error.detail || '未知错误'}`);
      }
    } catch (error) {
      console.error('Custom goals error:', error);
      alert('网络错误，请重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEnvironmentalInjection = async () => {
    if (!environmentalContext.trim()) {
      alert('请输入环境信息');
      return;
    }
    
    setIsSubmitting(true);
    try {
      const response = await fetch(`http://localhost:24861/api/v1/environment/inject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          environmental_context: environmentalContext
        })
      });
      
      if (response.ok) {
        alert('环境信息注入成功！');
        setEnvironmentalContext('');
        setShowEnvironmental(false);
      } else {
        const error = await response.json();
        alert(`注入失败: ${error.detail || '未知错误'}`);
      }
    } catch (error) {
      console.error('Environmental injection error:', error);
      alert('网络错误，请重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Load current custom goals when agent is selected
  React.useEffect(() => {
    if (selectedAgent) {
      fetch(`http://localhost:24861/api/v1/agents/${selectedAgent.agent_id}/custom_goals`)
        .then(response => response.json())
        .then(data => {
          setCustomGoals(data.custom_goals || '');
        })
        .catch(error => {
          console.error('Error loading custom goals:', error);
        });
    }
  }, [selectedAgent]);
  
  if (!selectedAgent) {
    return (
      <div className="panel">
        <h2>智能体详情</h2>
        <p style={{ color: '#666' }}>
          点击地图上的智能体查看详细信息
        </p>
      </div>
    );
  }
  
  const renderStatBar = (label, value, max, className) => (
    <div className="stat-bar">
      <div className="stat-label">{label}:</div>
      <div className="stat-value">
        <div 
          className={`stat-fill ${className}`}
          style={{ width: `${(value / max) * 100}%` }}
        />
      </div>
      <div className="stat-number">{value}</div>
    </div>
  );
  
  return (
    <div className="panel">
      <h2>智能体详情</h2>
      
      <div className="agent-details">
        <div className="agent-name">{selectedAgent.name}</div>
        <div className="agent-role">{selectedAgent.role === 'Guard' ? '狱警' : '囚犯'}</div>
        
        <div style={{ marginBottom: '15px' }}>
          <strong>位置:</strong> ({selectedAgent.position[0]}, {selectedAgent.position[1]})
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <strong>行动点:</strong> {selectedAgent.action_points}/3
        </div>
        
        {/* Custom Character Goals Section */}
        <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#2a4d3a', borderRadius: '5px' }}>
          <h3 style={{ color: '#4CAF50', fontSize: '14px', marginBottom: '10px' }}>📋 角色自定义目标</h3>
          
          {!showCustomGoals ? (
            <div>
              <div style={{ marginBottom: '10px', fontSize: '12px', color: '#ccc' }}>
                当前目标: {customGoals || '未设置'}
              </div>
              <button
                onClick={() => setShowCustomGoals(true)}
                style={{
                  padding: '6px 12px',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
                disabled={isSubmitting}
              >
                编辑角色目标
              </button>
            </div>
          ) : (
            <div>
              <textarea
                value={customGoals}
                onChange={(e) => setCustomGoals(e.target.value)}
                placeholder="输入这个角色的长期目标和动机..."
                style={{
                  width: '100%',
                  height: '80px',
                  padding: '8px',
                  backgroundColor: '#444',
                  color: '#fff',
                  border: '1px solid #666',
                  borderRadius: '3px',
                  fontSize: '12px',
                  resize: 'none',
                  marginBottom: '10px'
                }}
              />
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  onClick={handleSetCustomGoals}
                  disabled={isSubmitting}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: isSubmitting ? '#666' : '#4CAF50',
                    color: 'white',
                    border: 'none',
                    borderRadius: '3px',
                    fontSize: '12px',
                    cursor: isSubmitting ? 'not-allowed' : 'pointer'
                  }}
                >
                  {isSubmitting ? '保存中...' : '保存目标'}
                </button>
                <button
                  onClick={() => setShowCustomGoals(false)}
                  disabled={isSubmitting}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: '#666',
                    color: 'white',
                    border: 'none',
                    borderRadius: '3px',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  取消
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Environmental Injection Section */}
        <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#4a2c2a', borderRadius: '5px' }}>
          <h3 style={{ color: '#FF6B6B', fontSize: '14px', marginBottom: '10px' }}>🌍 环境注入</h3>
          
          {!showEnvironmental ? (
            <div>
              <div style={{ marginBottom: '10px', fontSize: '11px', color: '#ccc' }}>
                注入突发环境事件影响所有AI行为
              </div>
              <button
                onClick={() => setShowEnvironmental(true)}
                style={{
                  padding: '6px 12px',
                  backgroundColor: '#FF6B6B',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
                disabled={isSubmitting}
              >
                注入环境事件
              </button>
            </div>
          ) : (
            <div>
              <textarea
                value={environmentalContext}
                onChange={(e) => setEnvironmentalContext(e.target.value)}
                placeholder="例如: 突然停电，警报响起，外面传来喊叫声..."
                style={{
                  width: '100%',
                  height: '60px',
                  padding: '8px',
                  backgroundColor: '#444',
                  color: '#fff',
                  border: '1px solid #666',
                  borderRadius: '3px',
                  fontSize: '12px',
                  resize: 'none',
                  marginBottom: '10px'
                }}
              />
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  onClick={handleEnvironmentalInjection}
                  disabled={isSubmitting}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: isSubmitting ? '#666' : '#FF6B6B',
                    color: 'white',
                    border: 'none',
                    borderRadius: '3px',
                    fontSize: '12px',
                    cursor: isSubmitting ? 'not-allowed' : 'pointer'
                  }}
                >
                  {isSubmitting ? '注入中...' : '立即注入'}
                </button>
                <button
                  onClick={() => setShowEnvironmental(false)}
                  disabled={isSubmitting}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: '#666',
                    color: 'white',
                    border: 'none',
                    borderRadius: '3px',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  取消
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Goal Injection Section */}
        <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#333', borderRadius: '5px' }}>
          <h3 style={{ color: '#FFC107', fontSize: '14px', marginBottom: '10px' }}>🎯 临时目标注入</h3>
          
          {!showGoalInjection ? (
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button
                onClick={() => setShowGoalInjection(true)}
                style={{
                  padding: '6px 12px',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
                disabled={isSubmitting}
              >
                注入新目标
              </button>
              <button
                onClick={handleClearGoals}
                style={{
                  padding: '6px 12px',
                  backgroundColor: '#f44336',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
                disabled={isSubmitting}
              >
                清除手动目标
              </button>
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: '10px' }}>
                <label style={{ display: 'block', color: '#ccc', fontSize: '12px', marginBottom: '5px' }}>
                  目标名称:
                </label>
                <input
                  type="text"
                  value={goalName}
                  onChange={(e) => setGoalName(e.target.value)}
                  placeholder="例如: 寻找盟友"
                  style={{
                    width: '100%',
                    padding: '6px',
                    backgroundColor: '#444',
                    color: '#fff',
                    border: '1px solid #666',
                    borderRadius: '3px',
                    fontSize: '12px'
                  }}
                />
              </div>
              
              <div style={{ marginBottom: '10px' }}>
                <label style={{ display: 'block', color: '#ccc', fontSize: '12px', marginBottom: '5px' }}>
                  目标描述:
                </label>
                <textarea
                  value={goalDescription}
                  onChange={(e) => setGoalDescription(e.target.value)}
                  placeholder="详细描述这个目标..."
                  style={{
                    width: '100%',
                    height: '60px',
                    padding: '6px',
                    backgroundColor: '#444',
                    color: '#fff',
                    border: '1px solid #666',
                    borderRadius: '3px',
                    fontSize: '12px',
                    resize: 'none'
                  }}
                />
              </div>
              
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', color: '#ccc', fontSize: '12px', marginBottom: '5px' }}>
                  优先级 (1-10):
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={goalPriority}
                  onChange={(e) => setGoalPriority(parseInt(e.target.value) || 5)}
                  style={{
                    width: '60px',
                    padding: '6px',
                    backgroundColor: '#444',
                    color: '#fff',
                    border: '1px solid #666',
                    borderRadius: '3px',
                    fontSize: '12px'
                  }}
                />
              </div>
              
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  onClick={handleInjectGoal}
                  disabled={isSubmitting}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: isSubmitting ? '#666' : '#4CAF50',
                    color: 'white',
                    border: 'none',
                    borderRadius: '3px',
                    fontSize: '12px',
                    cursor: isSubmitting ? 'not-allowed' : 'pointer'
                  }}
                >
                  {isSubmitting ? '提交中...' : '注入目标'}
                </button>
                <button
                  onClick={() => {
                    setShowGoalInjection(false);
                    setGoalName('');
                    setGoalDescription('');
                    setGoalPriority(5);
                  }}
                  disabled={isSubmitting}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: '#666',
                    color: 'white',
                    border: 'none',
                    borderRadius: '3px',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  取消
                </button>
              </div>
            </div>
          )}
        </div>
        
        <h3>状态</h3>
        {renderStatBar('生命值', selectedAgent.hp, 100, 'hp')}
        {renderStatBar('理智值', selectedAgent.sanity, 100, 'sanity')}
        {renderStatBar('饥饿度', selectedAgent.hunger, 100, 'hunger')}
        {renderStatBar('干渴度', selectedAgent.thirst, 100, 'thirst')}
        {renderStatBar('力量', selectedAgent.strength, 100, 'strength')}
        
        {selectedAgent.status_tags.length > 0 && (
          <div>
            <h3>状态标签</h3>
            <div className="status-tags">
              {selectedAgent.status_tags.map(tag => (
                <span key={tag} className="status-tag">{tag}</span>
              ))}
            </div>
          </div>
        )}
        
        <h3>性格特质</h3>
        {renderStatBar('攻击性', selectedAgent.traits.aggression, 100, 'hp')}
        {renderStatBar('同理心', selectedAgent.traits.empathy, 100, 'sanity')}
        {renderStatBar('逻辑性', selectedAgent.traits.logic, 100, 'hunger')}
        {renderStatBar('服从性', selectedAgent.traits.obedience, 100, 'thirst')}
        {renderStatBar('韧性', selectedAgent.traits.resilience, 100, 'strength')}
        
        <h3>物品清单</h3>
        {selectedAgent.inventory.length > 0 ? (
          <div>
            {selectedAgent.inventory.map(item => (
              <div key={item.item_id} style={{
                padding: '5px',
                backgroundColor: '#444',
                marginBottom: '5px',
                borderRadius: '3px',
                fontSize: '12px'
              }}>
                <strong>{item.name}</strong><br />
                {item.description}
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#666', fontSize: '12px' }}>没有物品</p>
        )}
        
        <h3>人际关系</h3>
        {Object.keys(selectedAgent.relationships).length > 0 ? (
          <div>
            {Object.entries(selectedAgent.relationships).map(([targetId, relationship]) => {
              const targetAgent = worldState?.agents[targetId];
              return (
                <div key={targetId} style={{
                  padding: '8px',
                  backgroundColor: '#444',
                  marginBottom: '8px',
                  borderRadius: '3px',
                  fontSize: '12px'
                }}>
                  <div style={{ fontWeight: 'bold' }}>
                    {targetAgent?.name || targetId}
                  </div>
                  <div className="stat-bar">
                    <div className="stat-label">关系:</div>
                    <div className="stat-value">
                      <div 
                        className="stat-fill sanity"
                        style={{ width: `${relationship.score}%` }}
                      />
                    </div>
                    <div className="stat-number">{relationship.score}</div>
                  </div>
                  <div style={{ color: '#ccc', fontSize: '10px', marginTop: '5px' }}>
                    {relationship.context}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p style={{ color: '#666', fontSize: '12px' }}>没有关系</p>
        )}
        
        <h3>近期记忆</h3>
        {selectedAgent.memory.episodic.length > 0 ? (
          <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
            {selectedAgent.memory.episodic.slice(-10).reverse().map((memory, index) => (
              <div key={index} style={{
                padding: '5px',
                backgroundColor: '#444',
                marginBottom: '5px',
                borderRadius: '3px',
                fontSize: '11px',
                color: '#ccc'
              }}>
                {memory}
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#666', fontSize: '12px' }}>没有近期记忆</p>
        )}
        
        <h3>目标</h3>
        {selectedAgent.objectives.length > 0 ? (
          <div>
            {selectedAgent.objectives.map(objective => (
              <div key={objective.objective_id} style={{
                padding: '8px',
                backgroundColor: '#444',
                marginBottom: '8px',
                borderRadius: '3px',
                fontSize: '12px'
              }}>
                <div style={{ fontWeight: 'bold' }}>
                  {objective.name} ({objective.type})
                </div>
                <div style={{ color: '#ccc', fontSize: '10px' }}>
                  {objective.description}
                </div>
                <div style={{ 
                  color: objective.is_completed ? '#4CAF50' : '#FFC107',
                  fontSize: '10px',
                  marginTop: '5px'
                }}>
                  {objective.is_completed ? '已完成' : '进行中'}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#666', fontSize: '12px' }}>没有目标</p>
        )}
      </div>
    </div>
  );
}

export default DetailPanel;