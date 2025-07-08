/**
 * Prompt Panel component for displaying AI Agent prompts in real-time
 */
import React, { useState } from 'react';
import useWorldStore from '../store/worldStore';

function PromptPanel() {
  const { worldState } = useWorldStore();
  const [selectedAgentId, setSelectedAgentId] = useState(null);
  
  if (!worldState || !worldState.agent_prompts) {
    return (
      <div className="panel">
        <h2>AI Prompt 监控</h2>
        <p style={{ color: '#666' }}>
          等待Agent数据...
        </p>
      </div>
    );
  }

  const agentPrompts = worldState.agent_prompts;
  const agentIds = Object.keys(agentPrompts);

  const selectedPrompt = selectedAgentId ? agentPrompts[selectedAgentId] : null;

  return (
    <div className="panel" style={{ height: '100vh', overflow: 'hidden' }}>
      <h2>AI Prompt 监控</h2>
      
      {/* Agent Selector */}
      <div style={{ marginBottom: '15px' }}>
        <label style={{ color: '#ccc', fontSize: '12px' }}>选择Agent:</label>
        <select 
          value={selectedAgentId || ''} 
          onChange={(e) => setSelectedAgentId(e.target.value)}
          style={{
            width: '100%',
            marginTop: '5px',
            padding: '5px',
            backgroundColor: '#444',
            color: '#fff',
            border: '1px solid #666',
            borderRadius: '3px'
          }}
        >
          <option value="">-- 选择一个Agent --</option>
          {agentIds.map(agentId => (
            <option key={agentId} value={agentId}>
              {agentPrompts[agentId].agent_name} ({agentPrompts[agentId].timestamp})
            </option>
          ))}
        </select>
      </div>

      {/* Quick Overview */}
      <div style={{ marginBottom: '15px' }}>
        <h4 style={{ color: '#fff', fontSize: '14px' }}>快速概览</h4>
        <div style={{ maxHeight: '100px', overflowY: 'auto' }}>
          {agentIds.map(agentId => {
            const prompt = agentPrompts[agentId];
            return (
              <div 
                key={agentId} 
                style={{
                  padding: '3px 5px',
                  backgroundColor: selectedAgentId === agentId ? '#555' : '#333',
                  marginBottom: '2px',
                  borderRadius: '2px',
                  fontSize: '10px',
                  cursor: 'pointer',
                  border: selectedAgentId === agentId ? '1px solid #666' : 'none'
                }}
                onClick={() => setSelectedAgentId(agentId)}
              >
                <div style={{ fontWeight: 'bold', color: '#fff' }}>
                  {prompt.agent_name} ({prompt.timestamp})
                </div>
                <div style={{ color: '#ccc' }}>
                  Decision: {prompt.decision || 'Processing...'}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detailed View */}
      {selectedPrompt && (
        <div style={{ height: 'calc(100vh - 300px)', overflow: 'hidden' }}>
          <h4 style={{ color: '#fff', fontSize: '14px' }}>
            {selectedPrompt.agent_name} 详细信息 ({selectedPrompt.timestamp})
          </h4>
          
          <div style={{ height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {/* Thinking Process */}
            <div style={{ marginBottom: '10px' }}>
              <h5 style={{ color: '#4CAF50', fontSize: '12px', marginBottom: '5px' }}>
                🧠 思考过程:
              </h5>
              <div style={{
                backgroundColor: '#2d2d2d',
                padding: '8px',
                borderRadius: '4px',
                fontSize: '10px',
                color: '#ccc',
                maxHeight: '120px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
                border: '1px solid #444',
                minHeight: '40px'
              }}>
                {selectedPrompt.thinking_process || '等待AI思考过程...'}
              </div>
            </div>

            {/* Decision */}
            {selectedPrompt.decision && (
              <div style={{ marginBottom: '10px' }}>
                <h5 style={{ color: '#FF9800', fontSize: '12px', marginBottom: '5px' }}>
                  ⚡ 最终决策:
                </h5>
                <div style={{
                  backgroundColor: '#2d2d2d',
                  padding: '8px',
                  borderRadius: '4px',
                  fontSize: '10px',
                  color: '#fff',
                  fontFamily: 'monospace'
                }}>
                  {selectedPrompt.decision}
                </div>
              </div>
            )}

            {/* Full Prompt */}
            <div style={{ flex: 1, overflow: 'hidden', minHeight: '200px', display: 'flex', flexDirection: 'column' }}>
              <h5 style={{ color: '#2196F3', fontSize: '12px', marginBottom: '5px', flexShrink: 0 }}>
                📝 完整Prompt内容:
              </h5>
              <div style={{
                backgroundColor: '#1e1e1e',
                padding: '8px',
                borderRadius: '4px',
                fontSize: '9px',
                color: '#ccc',
                flex: 1,
                overflowY: 'auto',
                overflowX: 'hidden',
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace',
                lineHeight: '1.4',
                wordBreak: 'break-word',
                border: '1px solid #444',
                maxHeight: '400px'
              }}>
                {selectedPrompt.prompt_content || '暂无Prompt内容'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default PromptPanel;