/**
 * Experiment Control component - Left top panel
 * Controls experiment state, shows global status, handles environment injection
 */
import React, { useState, useEffect } from 'react';
import useWorldStore from '../store/worldStore';

function ExperimentControl() {
  const { worldState, startExperiment, stopExperiment, isConnected } = useWorldStore();
  const [environmentInjection, setEnvironmentInjection] = useState('');
  const [availableSessions, setAvailableSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState('');
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [experimentConfig, setExperimentConfig] = useState({
    guardCount: 2,
    prisonerCount: 4,
    durationDays: 14,
    model: 'anthropic/claude-3-haiku'
  });
  const [availableModels] = useState([
    { id: 'anthropic/claude-3-haiku', name: 'Claude 3 Haiku (快速)', cost: '低' },
    { id: 'anthropic/claude-3-sonnet', name: 'Claude 3 Sonnet (平衡)', cost: '中' },
    { id: 'anthropic/claude-3-opus', name: 'Claude 3 Opus (强大)', cost: '高' },
    { id: 'openai/gpt-4o-mini', name: 'GPT-4o Mini (快速)', cost: '低' },
    { id: 'openai/gpt-4o', name: 'GPT-4o (强大)', cost: '高' },
    { id: 'meta-llama/llama-3.1-70b-instruct', name: 'Llama 3.1 70B', cost: '中' },
    { id: 'google/gemini-pro-1.5', name: 'Gemini Pro 1.5', cost: '中' },
    
    // 新增免费模型
    { id: 'openrouter/cypher-alpha:free', name: 'Cypher Alpha (免费)', cost: '免费' },
    { id: 'deepseek/deepseek-r1-0528-qwen3-8b:free', name: 'DeepSeek R1 Qwen3 8B (免费)', cost: '免费' },
    { id: 'deepseek/deepseek-r1-0528:free', name: 'DeepSeek R1 (免费)', cost: '免费' },
    { id: 'qwen/qwen3-32b:free', name: 'Qwen3 32B (免费)', cost: '免费' }
  ]);
  
  // Load available sessions
  useEffect(() => {
    loadSessions();
  }, []);

  // Set current session as selected when available
  useEffect(() => {
    if (worldState?.session_id && !selectedSession) {
      setSelectedSession(worldState.session_id);
    }
  }, [worldState?.session_id, selectedSession]);

  const loadSessions = async () => {
    try {
      const response = await fetch('http://localhost:24861/api/v1/sessions');
      const sessions = await response.json();
      setAvailableSessions(sessions);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };
  
  const handleStartNew = () => {
    setShowConfigModal(true);
  };

  const handleConfirmStart = async () => {
    try {
      // Use the existing experiment/start API with configuration
      const response = await fetch('http://localhost:24861/api/v1/experiment/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          duration_days: experimentConfig.durationDays,
          agent_count: experimentConfig.guardCount + experimentConfig.prisonerCount,
          guard_count: experimentConfig.guardCount,
          prisoner_count: experimentConfig.prisonerCount,
          model: experimentConfig.model
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('New experiment started:', result);
        loadSessions(); // Refresh session list
        setShowConfigModal(false);
        
        // The backend handles starting the experiment and session creation
        alert('新实验已开始！');
      } else {
        const error = await response.text();
        console.error('Start experiment failed:', error);
        alert(`创建新实验失败: ${error}`);
      }
    } catch (error) {
      console.error('Error creating new experiment:', error);
      alert(`创建新实验失败: ${error.message}`);
    }
  };
  
  const handleContinue = () => {
    if (selectedSession && selectedSession !== worldState?.session_id) {
      // Switch to selected session and continue
      // This would need backend support to load a specific session
      alert('切换会话功能需要后端支持');
    } else {
      startExperiment();
    }
  };
  
  const handleStop = () => {
    stopExperiment();
  };
  
  const handleInjectEnvironment = async () => {
    if (!environmentInjection.trim()) return;
    
    try {
      const response = await fetch('http://localhost:24861/api/v1/environment/inject', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: environmentInjection
        })
      });
      
      if (response.ok) {
        setEnvironmentInjection('');
        alert('环境注入成功！');
      } else {
        alert('环境注入失败');
      }
    } catch (error) {
      console.error('Environment injection error:', error);
      alert('环境注入失败');
    }
  };
  
  const isRunning = worldState?.is_running || false;
  
  return (
    <div className="panel">
      <h2>🎯 实验控制台</h2>
      
      {/* Control Buttons */}
      <div className="form-group">
        <button 
          className="btn btn-success" 
          onClick={handleStartNew}
          disabled={!isConnected || isRunning}
          style={{ width: '48%', marginRight: '4%' }}
        >
          🆕 开始新实验
        </button>
        
        <button 
          className="btn" 
          onClick={handleContinue}
          disabled={!isConnected || isRunning}
          style={{ width: '48%', backgroundColor: '#17a2b8' }}
        >
          ▶️ 继续当前实验
        </button>
        
        <button 
          className="btn btn-danger" 
          onClick={handleStop}
          disabled={!isConnected || !isRunning}
          style={{ width: '100%', marginTop: '8px', padding: '6px' }}
        >
          ⏹️ 停止实验
        </button>
      </div>
      
      {/* Session Selection */}
      <div className="form-group">
        <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', color: '#ccc' }}>
          选择会话:
        </label>
        <select 
          value={selectedSession} 
          onChange={(e) => setSelectedSession(e.target.value)}
          style={{
            width: '100%',
            padding: '5px',
            backgroundColor: '#333',
            color: 'white',
            border: '1px solid #555',
            borderRadius: '3px',
            fontSize: '11px'
          }}
        >
          <option value="">选择会话...</option>
          {availableSessions.map(session => (
            <option key={session.session_id} value={session.session_id}>
              {session.session_id} ({session.start_time})
            </option>
          ))}
        </select>
        {selectedSession && selectedSession === worldState?.session_id && (
          <div style={{ fontSize: '10px', color: '#4caf50', marginTop: '3px' }}>
            ✓ 当前活跃会话
          </div>
        )}
      </div>
      
      {/* Global Status */}
      <h3>📊 实验状态</h3>
      <div style={{ 
        backgroundColor: '#333', 
        padding: '10px', 
        borderRadius: '4px',
        marginBottom: '15px' 
      }}>
        {worldState ? (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '13px' }}>
              <div>📅 天数: <strong>{worldState.day}</strong></div>
              <div>🕐 小时: <strong>{worldState.hour}</strong></div>
              <div>🤖 智能体: <strong>{Object.keys(worldState.agents).length}</strong></div>
              <div>🔄 状态: <strong style={{ color: isRunning ? '#4CAF50' : '#f44336' }}>
                {isRunning ? '运行中' : '已停止'}
              </strong></div>
            </div>
            {worldState.session_id && (
              <div style={{ fontSize: '10px', color: '#888', marginTop: '8px' }}>
                会话ID: {worldState.session_id}
              </div>
            )}
          </>
        ) : (
          <div style={{ color: '#666', textAlign: 'center' }}>等待连接...</div>
        )}
      </div>
      
      {/* Environment Injection */}
      <h3>🌍 环境注入</h3>
      <div className="form-group">
        <textarea
          value={environmentInjection}
          onChange={(e) => setEnvironmentInjection(e.target.value)}
          placeholder="输入环境事件或干预信息..."
          style={{
            minHeight: '80px',
            resize: 'vertical'
          }}
        />
        <button
          className="btn"
          onClick={handleInjectEnvironment}
          disabled={!isConnected || !environmentInjection.trim()}
          style={{ marginTop: '8px', width: '100%' }}
        >
          💉 注入环境事件
        </button>
      </div>
      
      {/* Connection Status */}
      <div style={{ 
        marginTop: '15px', 
        padding: '8px', 
        backgroundColor: isConnected ? '#1b5e20' : '#c62828',
        borderRadius: '4px',
        fontSize: '12px',
        textAlign: 'center'
      }}>
        {isConnected ? '🟢 已连接到服务器' : '🔴 未连接到服务器'}
      </div>

      {/* Configuration Modal */}
      {showConfigModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.8)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: '#2a2a2a',
            padding: '25px',
            borderRadius: '8px',
            border: '1px solid #555',
            minWidth: '350px',
            maxWidth: '90vw'
          }}>
            <h3 style={{ margin: '0 0 20px 0', color: '#fff' }}>⚙️ 实验配置</h3>
            
            <div className="form-group">
              <label>狱警数量:</label>
              <input
                type="number"
                min="1"
                max="10"
                value={experimentConfig.guardCount}
                onChange={(e) => setExperimentConfig({
                  ...experimentConfig,
                  guardCount: parseInt(e.target.value) || 1
                })}
              />
            </div>
            
            <div className="form-group">
              <label>囚犯数量:</label>
              <input
                type="number"
                min="1"
                max="20"
                value={experimentConfig.prisonerCount}
                onChange={(e) => setExperimentConfig({
                  ...experimentConfig,
                  prisonerCount: parseInt(e.target.value) || 1
                })}
              />
            </div>
            
            <div className="form-group">
              <label>实验天数:</label>
              <input
                type="number"
                min="1"
                max="30"
                value={experimentConfig.durationDays}
                onChange={(e) => setExperimentConfig({
                  ...experimentConfig,
                  durationDays: parseInt(e.target.value) || 1
                })}
              />
            </div>
            
            <div className="form-group">
              <label>AI模型:</label>
              <select
                value={experimentConfig.model}
                onChange={(e) => setExperimentConfig({
                  ...experimentConfig,
                  model: e.target.value
                })}
                style={{
                  width: '100%',
                  padding: '8px',
                  backgroundColor: '#333',
                  color: 'white',
                  border: '1px solid #555',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}
              >
                {availableModels.map(model => (
                  <option key={model.id} value={model.id}>
                    {model.name} - 成本: {model.cost}
                  </option>
                ))}
              </select>
              <div style={{ fontSize: '10px', marginTop: '4px' }}>
                <span style={{ color: '#888' }}>选择的模型: </span>
                <span style={{ 
                  color: availableModels.find(m => m.id === experimentConfig.model)?.cost === '免费' 
                    ? '#4CAF50' 
                    : '#ccc' 
                }}>
                  {availableModels.find(m => m.id === experimentConfig.model)?.name}
                </span>
                {availableModels.find(m => m.id === experimentConfig.model)?.cost === '免费' && (
                  <span style={{ 
                    marginLeft: '8px',
                    backgroundColor: '#4CAF50', 
                    color: 'white', 
                    padding: '1px 6px', 
                    borderRadius: '8px', 
                    fontSize: '8px',
                    fontWeight: 'bold'
                  }}>
                    FREE
                  </span>
                )}
              </div>
            </div>
            
            <div style={{ 
              display: 'flex', 
              gap: '10px', 
              marginTop: '20px',
              justifyContent: 'flex-end'
            }}>
              <button
                className="btn"
                onClick={() => setShowConfigModal(false)}
                style={{ backgroundColor: '#666' }}
              >
                取消
              </button>
              <button
                className="btn btn-success"
                onClick={handleConfirmStart}
                disabled={!isConnected}
              >
                开始实验
              </button>
            </div>
            
            <div style={{ 
              fontSize: '11px', 
              color: '#ccc', 
              marginTop: '15px',
              padding: '8px',
              backgroundColor: '#333',
              borderRadius: '4px'
            }}>
              总智能体: {experimentConfig.guardCount + experimentConfig.prisonerCount}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ExperimentControl;