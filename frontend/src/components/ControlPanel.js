/**
 * Control Panel component for experiment controls
 */
import React, { useState, useEffect } from 'react';
import useWorldStore from '../store/worldStore';

function ControlPanel() {
  const { worldState, startExperiment, stopExperiment, isConnected } = useWorldStore();
  const [recentEvents, setRecentEvents] = useState([]);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [eventsPerPage] = useState(20);
  const [totalEvents, setTotalEvents] = useState(0);
  const [availableSessions, setAvailableSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState('');
  
  const handleStart = () => {
    startExperiment();
  };
  
  const handleStop = () => {
    stopExperiment();
  };
  
  const isRunning = worldState?.is_running || false;

  // Load events from database with pagination
  const loadEvents = async (page = 0) => {
    setLoadingEvents(true);
    try {
      const offset = page * eventsPerPage;
      
      // Get current session ID if world state is available
      let sessionParam = '';
      if (worldState?.session_id) {
        sessionParam = `&session_id=${worldState.session_id}`;
      }
      
      const response = await fetch(`http://localhost:24861/api/v1/events?limit=1000&offset=${offset}${sessionParam}`);
      const data = await response.json();
      
      // Get all events and group by time
      const events = data.events || [];
      setTotalEvents(events.length);
      
      // Group events by time (day, hour, minute)
      const timelineData = groupEventsByTime(events);
      setRecentEvents(timelineData);
    } catch (error) {
      console.error('Error loading events:', error);
    } finally {
      setLoadingEvents(false);
    }
  };
  
  // Group events by time and organize by agents
  const groupEventsByTime = (events) => {
    const timeGroups = {};
    
    // Group events by time
    events.forEach(event => {
      const timeKey = `${event.day}_${event.hour}_${event.minute}`;
      if (!timeGroups[timeKey]) {
        timeGroups[timeKey] = {
          day: event.day,
          hour: event.hour,
          minute: event.minute,
          agents: {}
        };
      }
      
      if (!timeGroups[timeKey].agents[event.agent_name]) {
        timeGroups[timeKey].agents[event.agent_name] = [];
      }
      
      timeGroups[timeKey].agents[event.agent_name].push({
        description: event.description,
        event_type: event.event_type,
        timestamp: event.timestamp
      });
    });
    
    // Convert to array and sort by time (latest first)
    return Object.values(timeGroups).sort((a, b) => {
      if (a.day !== b.day) return b.day - a.day;
      if (a.hour !== b.hour) return b.hour - a.hour;
      return b.minute - a.minute;
    }).slice(currentPage * eventsPerPage, (currentPage + 1) * eventsPerPage);
  };

  // Load events when component mounts and periodically refresh
  useEffect(() => {
    loadEvents(currentPage);
    loadSessions();
    
    // Refresh events every 5 seconds when experiment is running
    const interval = isRunning ? setInterval(() => loadEvents(currentPage), 5000) : null;
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunning, currentPage, worldState?.session_id]);

  // Set current session as selected when available
  useEffect(() => {
    if (worldState?.session_id && !selectedSession) {
      setSelectedSession(worldState.session_id);
    }
  }, [worldState?.session_id, selectedSession]);
  
  // Get unique agent names for columns
  const getAgentNames = () => {
    if (!worldState?.agents) return [];
    return Object.values(worldState.agents).map(agent => agent.name).sort();
  };

  const getEventTypeColor = (type) => {
    const colors = {
      'rest': '#666',
      'move': '#2196F3',
      'speak': '#4CAF50',
      'attack': '#f44336',
      'use_item': '#FF9800',
      'system': '#9C27B0'
    };
    return colors[type] || '#ccc';
  };

  // Load available sessions
  const loadSessions = async () => {
    try {
      const response = await fetch('http://localhost:24861/api/v1/sessions');
      const sessions = await response.json();
      setAvailableSessions(sessions);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  // Export functions
  const exportEvents = async (format) => {
    try {
      const sessionParam = selectedSession ? `?session_id=${selectedSession}` : '';
      const response = await fetch(`http://localhost:24861/api/v1/events/export/${format}${sessionParam}`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = response.headers.get('Content-Disposition')?.split('filename=')[1] || `events.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        console.error('Export failed:', response.statusText);
      }
    } catch (error) {
      console.error('Export error:', error);
    }
  };

  const downloadSessionSummary = async () => {
    if (!selectedSession) return;
    
    try {
      const response = await fetch(`http://localhost:24861/api/v1/sessions/${selectedSession}/summary`);
      const data = await response.json();
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `session_${selectedSession}_summary.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Summary download error:', error);
    }
  };
  
  return (
    <div className="panel">
      <h2>实验控制</h2>
      
      <div className="form-group">
        <button 
          className="btn btn-success" 
          onClick={handleStart}
          disabled={!isConnected || isRunning}
        >
          开始实验
        </button>
        
        <button 
          className="btn btn-danger" 
          onClick={handleStop}
          disabled={!isConnected || !isRunning}
        >
          停止实验
        </button>
      </div>
      
      <h3>全局状态</h3>
      {worldState && (
        <div>
          <p>天数: {worldState.day}</p>
          <p>小时: {worldState.hour}</p>
          <p>智能体数量: {Object.keys(worldState.agents).length}</p>
          <p>状态: {isRunning ? '运行中' : '已停止'}</p>
          {worldState.session_id && (
            <p style={{ fontSize: '10px', color: '#888' }}>
              实验会话ID: {worldState.session_id}
            </p>
          )}
        </div>
      )}
      
      <h3>智能体概览</h3>
      {worldState && (
        <div>
          {Object.values(worldState.agents).map(agent => (
            <div key={agent.agent_id} style={{ 
              marginBottom: '10px',
              padding: '8px',
              backgroundColor: '#333',
              borderRadius: '4px',
              fontSize: '12px'
            }}>
              <div style={{ fontWeight: 'bold' }}>
                {agent.name} ({agent.role === 'Guard' ? '狱警' : '囚犯'})
              </div>
              <div style={{ color: '#ccc' }}>
                生命值: {agent.hp} | 理智值: {agent.sanity} | 
                位置: ({agent.position[0]}, {agent.position[1]})
              </div>
              {agent.status_tags.length > 0 && (
                <div className="status-tags">
                  {agent.status_tags.map(tag => (
                    <span key={tag} className="status-tag">{tag}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      
      <h3>数据导出</h3>
      <div style={{ marginBottom: '15px' }}>
        <div style={{ marginBottom: '10px' }}>
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
            <option value="">所有会话</option>
            {availableSessions.map(session => (
              <option key={session.session_id} value={session.session_id}>
                {session.session_id} ({session.start_time})
              </option>
            ))}
          </select>
        </div>
        
        <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
          <button
            onClick={() => exportEvents('csv')}
            style={{
              padding: '6px 12px',
              backgroundColor: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              fontSize: '11px',
              cursor: 'pointer'
            }}
          >
            导出 CSV
          </button>
          
          <button
            onClick={() => exportEvents('json')}
            style={{
              padding: '6px 12px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              fontSize: '11px',
              cursor: 'pointer'
            }}
          >
            导出 JSON
          </button>
          
          {selectedSession && (
            <button
              onClick={downloadSessionSummary}
              style={{
                padding: '6px 12px',
                backgroundColor: '#FF9800',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                fontSize: '11px',
                cursor: 'pointer'
              }}
            >
              会话摘要
            </button>
          )}
        </div>
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <h3 style={{ margin: 0 }}>最近事件</h3>
        <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
          <button
            onClick={() => loadEvents(currentPage)}
            disabled={loadingEvents}
            style={{
              padding: '4px 8px',
              backgroundColor: loadingEvents ? '#666' : '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              fontSize: '11px',
              cursor: loadingEvents ? 'not-allowed' : 'pointer'
            }}
          >
            {loadingEvents ? '加载中...' : '刷新'}
          </button>
          
          <span style={{ fontSize: '10px', color: '#ccc' }}>
            总计: {totalEvents} | 页: {currentPage + 1}
          </span>
        </div>
      </div>
      <div style={{ height: '400px', overflow: 'hidden' }}>
        {loadingEvents ? (
          <div style={{ color: '#ccc', textAlign: 'center', padding: '20px' }}>
            加载中...
          </div>
        ) : recentEvents.length === 0 ? (
          <div style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
            暂无事件记录
          </div>
        ) : (
          <div style={{ 
            height: '100%', 
            overflowY: 'auto',
            backgroundColor: '#222',
            borderRadius: '5px',
            padding: '5px'
          }}>
            {/* Timeline Table Header */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: `80px ${getAgentNames().map(() => '1fr').join(' ')}`,
              gap: '3px',
              padding: '6px 3px',
              backgroundColor: '#444',
              borderRadius: '3px',
              marginBottom: '5px',
              fontSize: '10px',
              fontWeight: 'bold',
              color: '#fff',
              position: 'sticky',
              top: '0',
              zIndex: 1
            }}>
              <div style={{ textAlign: 'center' }}>时间</div>
              {getAgentNames().map(agentName => (
                <div key={agentName} style={{ 
                  textAlign: 'center',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {agentName}
                </div>
              ))}
            </div>
            
            {/* Timeline Rows */}
            {recentEvents.map((timeSlot, index) => (
              <div
                key={`${timeSlot.day}-${timeSlot.hour}-${timeSlot.minute}`}
                style={{
                  display: 'grid',
                  gridTemplateColumns: `80px ${getAgentNames().map(() => '1fr').join(' ')}`,
                  gap: '3px',
                  padding: '4px 3px',
                  backgroundColor: index % 2 === 0 ? '#2a2a2a' : '#333',
                  borderRadius: '3px',
                  marginBottom: '2px',
                  fontSize: '9px',
                  minHeight: '24px',
                  alignItems: 'center'
                }}
              >
                {/* Time Column */}
                <div style={{ 
                  color: '#fff', 
                  fontFamily: 'monospace',
                  textAlign: 'center',
                  fontWeight: 'bold'
                }}>
                  D{timeSlot.day}H{timeSlot.hour}M{timeSlot.minute}
                </div>
                
                {/* Agent Action Columns */}
                {getAgentNames().map(agentName => {
                  const agentActions = timeSlot.agents[agentName] || [];
                  return (
                    <div 
                      key={agentName}
                      style={{ 
                        minHeight: '20px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '1px'
                      }}
                    >
                      {agentActions.length === 0 ? (
                        <div style={{ 
                          color: '#555',
                          textAlign: 'center',
                          fontSize: '8px'
                        }}>
                          -
                        </div>
                      ) : (
                        agentActions.map((action, actionIndex) => (
                          <div
                            key={actionIndex}
                            style={{
                              padding: '1px 3px',
                              backgroundColor: getEventTypeColor(action.event_type),
                              color: 'white',
                              borderRadius: '2px',
                              fontSize: '8px',
                              textAlign: 'center',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              opacity: 0.9
                            }}
                            title={`${agentName}: ${action.description}`}
                          >
                            {action.description.length > 20 
                              ? action.description.substring(0, 17) + '...'
                              : action.description
                            }
                          </div>
                        ))
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
            
            {/* Pagination Controls */}
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              gap: '10px',
              padding: '10px',
              position: 'sticky',
              bottom: '0',
              backgroundColor: '#222'
            }}>
              <button
                onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                disabled={currentPage === 0 || loadingEvents}
                style={{
                  padding: '4px 8px',
                  backgroundColor: currentPage === 0 ? '#555' : '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  fontSize: '10px',
                  cursor: currentPage === 0 ? 'not-allowed' : 'pointer'
                }}
              >
                上一页
              </button>
              
              <button
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={recentEvents.length < eventsPerPage || loadingEvents}
                style={{
                  padding: '4px 8px',
                  backgroundColor: recentEvents.length < eventsPerPage ? '#555' : '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  fontSize: '10px',
                  cursor: recentEvents.length < eventsPerPage ? 'not-allowed' : 'pointer'
                }}
              >
                下一页
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ControlPanel;