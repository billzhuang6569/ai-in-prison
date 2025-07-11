/**
 * Turn Indicator - 回合指示器组件
 * 显示当前正在执行动作的智能体，类似文明6的回合系统
 */
import React, { useState, useEffect } from 'react';
import useWorldStore from '../store/worldStore';

const API_BASE = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:24861';

function TurnIndicator() {
  const { worldState } = useWorldStore();
  const [currentActiveAgent, setCurrentActiveAgent] = useState(null);
  const [lastAgentName, setLastAgentName] = useState(null);
  const [turnCounter, setTurnCounter] = useState(0);
  
  // 获取最近活动的智能体
  const fetchCurrentActiveAgent = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/events?limit=20`);
      const data = await response.json();
      
      if (data.success !== false && data.events && data.events.length > 0) {
        // 查找最近的非系统事件，过滤掉过时的事件
        const currentWorldTime = worldState?.day * 24 + (worldState?.hour || 0);
        
        const recentEvent = data.events.find(event => {
          if (!event.agent_name || 
              event.agent_name === 'Research Team' || 
              event.agent_name === 'SYSTEM' ||
              event.event_type === 'item_placement') {
            return false;
          }
          
          // 只考虑当前世界时间附近的事件（前后2小时内）
          const eventTime = event.day * 24 + event.hour;
          return Math.abs(eventTime - currentWorldTime) <= 2;
        });
        
        if (recentEvent) {
          // 如果智能体发生变化，更新活跃智能体
          if (recentEvent.agent_name !== lastAgentName) {
            setLastAgentName(recentEvent.agent_name);
            
            // 根据agent_name找到对应的agent
            const activeAgent = Object.values(worldState?.agents || {}).find(agent => 
              agent.name === recentEvent.agent_name
            );
            
            if (activeAgent) {
              console.log(`🎯 Turn indicator: Switching to ${activeAgent.name} (${activeAgent.agent_id})`);
              setCurrentActiveAgent(activeAgent.agent_id);
              setTurnCounter(prev => prev + 1); // 增加回合计数器
            }
          }
        } else {
          // 如果没有找到最近的事件，使用循环模式
          if (worldState?.agents) {
            const agents = Object.values(worldState.agents);
            const currentIndex = turnCounter % agents.length;
            const selectedAgent = agents[currentIndex];
            
            if (selectedAgent && selectedAgent.agent_id !== currentActiveAgent) {
              setCurrentActiveAgent(selectedAgent.agent_id);
              setLastAgentName(selectedAgent.name);
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch current active agent:', error);
      
      // 错误情况下使用简单的循环模式
      if (worldState?.agents) {
        const agents = Object.values(worldState.agents);
        const currentIndex = Math.floor(Date.now() / 10000) % agents.length; // 每10秒切换
        const selectedAgent = agents[currentIndex];
        
        if (selectedAgent && selectedAgent.agent_id !== currentActiveAgent) {
          setCurrentActiveAgent(selectedAgent.agent_id);
          setLastAgentName(selectedAgent.name);
        }
      }
    }
  };
  
  // 定期检查当前活跃智能体
  useEffect(() => {
    if (!worldState?.agents) return;
    
    fetchCurrentActiveAgent();
    
    // 如果实验正在运行，每5秒检查一次
    if (worldState.is_running) {
      const interval = setInterval(fetchCurrentActiveAgent, 5000);
      return () => clearInterval(interval);
    }
  }, [worldState?.is_running, worldState?.agents, worldState?.day, worldState?.hour]);
  
  // 当世界时间变化时，自动切换到下一个智能体（备用机制）
  useEffect(() => {
    if (worldState?.agents && worldState?.is_running) {
      const agents = Object.values(worldState.agents);
      // 基于当前时间计算应该活跃的智能体
      const timeBasedIndex = (worldState.day * 24 + worldState.hour) % agents.length;
      const timeBasedAgent = agents[timeBasedIndex];
      
      if (timeBasedAgent && timeBasedAgent.agent_id !== currentActiveAgent) {
        // 延迟切换，给事件检测一些时间
        setTimeout(() => {
          if (currentActiveAgent === null || Math.random() > 0.7) { // 30%概率强制切换
            console.log(`⏰ Time-based switch to ${timeBasedAgent.name} at Day ${worldState.day} Hour ${worldState.hour}`);
            setCurrentActiveAgent(timeBasedAgent.agent_id);
            setLastAgentName(timeBasedAgent.name);
          }
        }, 2000);
      }
    }
  }, [worldState?.day, worldState?.hour]);
  
  if (!worldState?.agents) {
    return null;
  }
  
  const agents = Object.values(worldState.agents);
  const guards = agents.filter(agent => agent.role === 'Guard');
  const prisoners = agents.filter(agent => agent.role === 'Prisoner');
  
  // 使用动态检测的当前活跃智能体
  const currentAgent = currentActiveAgent ? 
    agents.find(agent => agent.agent_id === currentActiveAgent) : 
    agents[0]; // 默认第一个智能体
  
  return (
    <div className="turn-indicator">
      <div className="turn-indicator-title">
        🎯 当前回合
      </div>
      <div className="agent-icons-row">
        {/* 显示所有智能体图标 */}
        {[...guards, ...prisoners].map((agent, index) => {
          const isGuard = agent.role === 'Guard';
          const roleIndex = isGuard 
            ? guards.findIndex(g => g.agent_id === agent.agent_id) + 1
            : prisoners.findIndex(p => p.agent_id === agent.agent_id) + 1;
          
          const label = isGuard ? `G${roleIndex}` : `P${roleIndex}`;
          const isActive = currentAgent && currentAgent.agent_id === agent.agent_id;
          
          return (
            <div
              key={agent.agent_id}
              className={`agent-turn-icon ${agent.role} ${isActive ? 'active' : ''}`}
              style={{
                transform: isActive ? 'scale(1.3)' : 'scale(1)',
                transition: 'transform 0.3s ease'
              }}
              title={`${agent.name} (${agent.role})\nHP: ${agent.hp} | 理智: ${agent.sanity}\n饥饿: ${agent.hunger} | 口渴: ${agent.thirst}`}
            >
              {label}
              {isActive && (
                <div className="turn-indicator-pulse"></div>
              )}
            </div>
          );
        })}
      </div>
      
      {currentAgent && (
        <div className="current-agent-info">
          <span className="current-agent-name">
            {currentAgent.name}
          </span>
          <div className="current-agent-status">
            ❤️{currentAgent.hp} | 🧠{currentAgent.sanity} | 🍞{currentAgent.hunger} | 💧{currentAgent.thirst}
          </div>
          <div className="current-world-time">
            当前时间: Day {worldState.day} Hour {worldState.hour}
            {worldState.minute > 0 && ` Minute ${worldState.minute}`}
          </div>
        </div>
      )}
      
      <style jsx>{`
        .turn-indicator {
          background: linear-gradient(135deg, #2c3e50, #3498db);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 12px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
          border: 1px solid #34495e;
          contain: layout;
          will-change: auto;
        }
        
        .turn-indicator-title {
          color: #ecf0f1;
          font-size: 14px;
          font-weight: bold;
          text-align: center;
          margin-bottom: 8px;
          text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }
        
        .agent-icons-row {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          flex-wrap: wrap;
        }
        
        .agent-turn-icon {
          position: relative;
          width: 28px;
          height: 28px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: bold;
          color: white;
          text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.7);
          cursor: pointer;
          border: 2px solid transparent;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .agent-turn-icon.Guard {
          background: linear-gradient(135deg, #3498db, #2980b9);
        }
        
        .agent-turn-icon.Prisoner {
          background: linear-gradient(135deg, #f39c12, #d68910);
        }
        
        .agent-turn-icon.active {
          border-color: #f1c40f;
          box-shadow: 0 0 12px rgba(241, 196, 64, 0.6), 0 2px 4px rgba(0, 0, 0, 0.3);
          animation: glow 2s ease-in-out infinite alternate;
        }
        
        .turn-indicator-pulse {
          position: absolute;
          top: -3px;
          right: -3px;
          width: 8px;
          height: 8px;
          background-color: #e74c3c;
          border-radius: 50%;
          animation: pulse 1s ease-in-out infinite;
        }
        
        .current-agent-info {
          text-align: center;
          color: #ecf0f1;
        }
        
        .current-agent-name {
          font-size: 13px;
          font-weight: bold;
          display: block;
          margin-bottom: 2px;
          color: #f1c40f;
          text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.5);
        }
        
        .current-agent-status {
          font-size: 10px;
          color: #bdc3c7;
          display: flex;
          justify-content: center;
          gap: 8px;
          flex-wrap: wrap;
        }
        
        .current-world-time {
          font-size: 8px;
          color: #95a5a6;
          text-align: center;
          margin-top: 2px;
          font-style: italic;
          font-weight: bold;
        }
        
        @keyframes glow {
          from {
            box-shadow: 0 0 12px rgba(241, 196, 64, 0.6), 0 2px 4px rgba(0, 0, 0, 0.3);
          }
          to {
            box-shadow: 0 0 20px rgba(241, 196, 64, 0.8), 0 2px 4px rgba(0, 0, 0, 0.3);
          }
        }
        
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.7;
            transform: scale(1.2);
          }
        }
        
        .agent-turn-icon:hover {
          transform: scale(1.1) !important;
          transition: transform 0.2s ease;
        }
      `}</style>
    </div>
  );
}

export default TurnIndicator;