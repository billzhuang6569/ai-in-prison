/**
 * Experiment Milestones Component - 实验里程碑播报
 * 监听并播报重要实验事件
 */
import React, { useState, useEffect } from 'react';
import useWorldStore from '../store/worldStore';
import { Icon } from '@iconify/react';

const ExperimentMilestones = () => {
  const { worldState } = useWorldStore();
  const [milestones, setMilestones] = useState([]);
  const [isExpanded, setIsExpanded] = useState(true);
  const [lastProcessedEventId, setLastProcessedEventId] = useState(0);

  // 重要事件类型配置 - 使用Game Icons
  const importantEventTypes = {
    'attack': {
      icon: 'game-icons:crossed-swords',
      color: '#ff4444',
      priority: 'high',
      title: '攻击事件'
    },
    'speak': {
      icon: 'game-icons:conversation',
      color: '#4CAF50',
      priority: 'medium',
      title: '对话事件'
    },
    'death': {
      icon: 'game-icons:skull',
      color: '#000000',
      priority: 'critical',
      title: '死亡事件'
    },
    'rule_announcement': {
      icon: 'game-icons:megaphone',
      color: '#ff9800',
      priority: 'high',
      title: '规则宣布'
    },
    'item_placement': {
      icon: 'game-icons:chest',
      color: '#2196F3',
      priority: 'low',
      title: '道具投放'
    },
    'alliance': {
      icon: 'game-icons:handshake',
      color: '#9C27B0',
      priority: 'high',
      title: '联盟形成'
    },
    'tunnel_success': {
      icon: 'game-icons:hole',
      color: '#795548',
      priority: 'critical',
      title: '地道挖掘成功'
    },
    'emergency_assembly': {
      icon: 'game-icons:siren',
      color: '#f44336',
      priority: 'high',
      title: '紧急集合'
    },
    'theft': {
      icon: 'game-icons:stealing',
      color: '#FF5722',
      priority: 'medium',
      title: '偷窃事件'
    },
    'punishment': {
      icon: 'game-icons:scales',
      color: '#607D8B',
      priority: 'medium',
      title: '惩罚执行'
    }
  };

  // 监听事件并添加里程碑
  useEffect(() => {
    if (!worldState?.session_id) return;

    const checkNewEvents = async () => {
      try {
        const response = await fetch(
          `http://localhost:24861/api/v1/events?limit=20&session_id=${worldState.session_id}&offset=0`
        );
        const data = await response.json();

        // 过滤出新的重要事件
        const newEvents = data.events.filter(event => 
          event.id > lastProcessedEventId && 
          importantEventTypes[event.event_type]
        );

        if (newEvents.length > 0) {
          const newMilestones = newEvents.map(event => {
            const eventConfig = importantEventTypes[event.event_type];
            return {
              id: event.id,
              timestamp: new Date(event.timestamp),
              day: event.day,
              hour: event.hour,
              minute: event.minute,
              agentName: event.agent_name,
              eventType: event.event_type,
              description: event.description,
              details: event.details,
              icon: eventConfig.icon,
              color: eventConfig.color,
              priority: eventConfig.priority,
              title: eventConfig.title,
              isNew: true
            };
          }).reverse(); // 最新的在前

          setMilestones(prev => {
            const updated = [...newMilestones, ...prev].slice(0, 50); // 保留最近50个
            return updated;
          });

          // 更新最后处理的事件ID
          setLastProcessedEventId(Math.max(...newEvents.map(e => e.id)));

          // 3秒后移除"新事件"标记
          setTimeout(() => {
            setMilestones(prev => 
              prev.map(m => ({ ...m, isNew: false }))
            );
          }, 3000);
        }
      } catch (error) {
        console.error('Error fetching events for milestones:', error);
      }
    };

    // 初始加载
    checkNewEvents();

    // 每5秒检查新事件
    const interval = setInterval(checkNewEvents, 5000);

    return () => clearInterval(interval);
  }, [worldState?.session_id, lastProcessedEventId]);

  // 根据优先级排序
  const sortedMilestones = milestones.sort((a, b) => {
    const priorityOrder = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };
    if (priorityOrder[a.priority] !== priorityOrder[b.priority]) {
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    }
    return new Date(b.timestamp) - new Date(a.timestamp);
  });

  return (
    <div 
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '420px', // 避免与道具栏重叠
        backgroundColor: '#1a1a1a',
        border: '1px solid #444',
        borderRadius: '8px',
        minWidth: isExpanded ? '350px' : '60px',
        maxHeight: isExpanded ? '400px' : '60px',
        overflow: 'hidden',
        transition: 'all 0.3s ease',
        zIndex: 99,
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)'
      }}
    >
      {/* 标题栏 */}
      <div 
        style={{
          height: '60px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 15px',
          cursor: 'pointer',
          borderBottom: isExpanded ? '1px solid #444' : 'none',
          backgroundColor: '#2a2a2a'
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Icon icon="game-icons:target-arrows" width="24" height="24" style={{ color: 'white' }} />
          {isExpanded && (
            <span style={{ color: 'white', fontSize: '14px', fontWeight: 'bold' }}>
              实验里程碑
            </span>
          )}
        </div>
        {milestones.length > 0 && (
          <div style={{
            backgroundColor: '#ff4444',
            color: 'white',
            borderRadius: '12px',
            padding: '2px 8px',
            fontSize: '11px',
            fontWeight: 'bold'
          }}>
            {milestones.length}
          </div>
        )}
      </div>

      {/* 里程碑列表 */}
      {isExpanded && (
        <div 
          style={{
            padding: '10px',
            overflowY: 'auto',
            maxHeight: '340px',
            backgroundColor: '#1a1a1a'
          }}
        >
          {sortedMilestones.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              color: '#666', 
              fontSize: '12px',
              padding: '20px'
            }}>
              暂无重要事件
            </div>
          ) : (
            sortedMilestones.map((milestone) => (
              <div
                key={milestone.id}
                style={{
                  marginBottom: '8px',
                  padding: '10px',
                  backgroundColor: milestone.isNew ? 'rgba(76, 175, 80, 0.1)' : '#2a2a2a',
                  border: milestone.isNew ? '1px solid #4CAF50' : '1px solid #444',
                  borderRadius: '6px',
                  fontSize: '11px',
                  color: 'white',
                  position: 'relative',
                  animation: milestone.isNew ? 'pulse 2s infinite' : 'none'
                }}
              >
                {/* 优先级指示器 */}
                <div style={{
                  position: 'absolute',
                  left: '0',
                  top: '0',
                  bottom: '0',
                  width: '4px',
                  backgroundColor: milestone.color,
                  borderRadius: '6px 0 0 6px'
                }} />

                {/* 事件头部 */}
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '6px',
                  marginBottom: '4px'
                }}>
                  <Icon icon={milestone.icon} width="14" height="14" style={{ color: milestone.color }} />
                  <span style={{ 
                    fontWeight: 'bold',
                    color: milestone.color,
                    fontSize: '10px'
                  }}>
                    {milestone.title}
                  </span>
                  <span style={{ 
                    marginLeft: 'auto',
                    fontSize: '9px',
                    color: '#888'
                  }}>
                    Day {milestone.day} {milestone.hour}:{String(milestone.minute || 0).padStart(2, '0')}
                  </span>
                </div>

                {/* 事件内容 */}
                <div style={{ 
                  fontSize: '10px',
                  lineHeight: '1.3',
                  color: '#ccc',
                  marginLeft: '20px'
                }}>
                  <strong>{milestone.agentName}</strong>: {milestone.description}
                </div>

                {/* 新事件标记 */}
                {milestone.isNew && (
                  <div style={{
                    position: 'absolute',
                    top: '5px',
                    right: '5px',
                    backgroundColor: '#4CAF50',
                    color: 'white',
                    fontSize: '8px',
                    padding: '1px 4px',
                    borderRadius: '3px',
                    fontWeight: 'bold'
                  }}>
                    NEW
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* CSS动画 */}
      <style jsx>{`
        @keyframes pulse {
          0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7); }
          70% { box-shadow: 0 0 0 5px rgba(76, 175, 80, 0); }
          100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
        }
      `}</style>
    </div>
  );
};

export default ExperimentMilestones;