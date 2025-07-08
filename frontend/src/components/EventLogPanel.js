/**
 * Event Log Panel for displaying complete event history
 */
import React, { useState, useEffect } from 'react';

function EventLogPanel() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState({
    agent_id: '',
    event_type: '',
    day: ''
  });
  const [agents, setAgents] = useState([]);
  const [eventTypes, setEventTypes] = useState([]);
  const [stats, setStats] = useState({});
  
  // Load events
  const loadEvents = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter.agent_id) params.append('agent_id', filter.agent_id);
      if (filter.event_type) params.append('event_type', filter.event_type);
      if (filter.day) params.append('day', filter.day);
      params.append('limit', '200');
      
      const response = await fetch(`http://localhost:24861/api/v1/events?${params}`);
      const data = await response.json();
      
      setEvents(data.events || []);
      
      // Extract unique agents and event types for filtering
      const uniqueAgents = [...new Set(data.events.map(e => e.agent_name))];
      const uniqueTypes = [...new Set(data.events.map(e => e.event_type))];
      setAgents(uniqueAgents);
      setEventTypes(uniqueTypes);
      
    } catch (error) {
      console.error('Error loading events:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Load stats
  const loadStats = async () => {
    try {
      const response = await fetch('http://localhost:24861/api/v1/events/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };
  
  // Load data on component mount and when filters change
  useEffect(() => {
    loadEvents();
    loadStats();
  }, [filter]);
  
  const clearEvents = async () => {
    if (!window.confirm('确定要清除所有事件记录吗？')) {
      return;
    }
    
    try {
      await fetch('http://localhost:24861/api/v1/events/clear', { method: 'DELETE' });
      setEvents([]);
      setStats({});
      alert('事件记录已清除');
    } catch (error) {
      console.error('Error clearing events:', error);
      alert('清除失败');
    }
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
  
  return (
    <div className="panel" style={{ height: '100vh', overflow: 'hidden' }}>
      <h2>📋 事件日志</h2>
      
      {/* Stats Summary */}
      <div style={{ marginBottom: '15px', padding: '10px', backgroundColor: '#333', borderRadius: '5px' }}>
        <div style={{ fontSize: '12px', color: '#ccc' }}>
          总事件: {stats.total_events || 0} | 
          最近加载: {events.length} 条
        </div>
      </div>
      
      {/* Filters */}
      <div style={{ marginBottom: '15px', padding: '10px', backgroundColor: '#444', borderRadius: '5px' }}>
        <h4 style={{ color: '#fff', fontSize: '12px', marginBottom: '10px' }}>筛选条件</h4>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginBottom: '10px' }}>
          <select
            value={filter.agent_id}
            onChange={(e) => setFilter({...filter, agent_id: e.target.value})}
            style={{
              padding: '4px',
              backgroundColor: '#555',
              color: '#fff',
              border: '1px solid #666',
              borderRadius: '3px',
              fontSize: '11px'
            }}
          >
            <option value="">所有Agent</option>
            {agents.map(agent => (
              <option key={agent} value={agent}>{agent}</option>
            ))}
          </select>
          
          <select
            value={filter.event_type}
            onChange={(e) => setFilter({...filter, event_type: e.target.value})}
            style={{
              padding: '4px',
              backgroundColor: '#555',
              color: '#fff',
              border: '1px solid #666',
              borderRadius: '3px',
              fontSize: '11px'
            }}
          >
            <option value="">所有类型</option>
            {eventTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          
          <input
            type="number"
            placeholder="天数"
            value={filter.day}
            onChange={(e) => setFilter({...filter, day: e.target.value})}
            style={{
              padding: '4px',
              backgroundColor: '#555',
              color: '#fff',
              border: '1px solid #666',
              borderRadius: '3px',
              fontSize: '11px'
            }}
          />
        </div>
        
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => setFilter({ agent_id: '', event_type: '', day: '' })}
            style={{
              padding: '4px 8px',
              backgroundColor: '#666',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              fontSize: '11px',
              cursor: 'pointer'
            }}
          >
            清除筛选
          </button>
          
          <button
            onClick={clearEvents}
            style={{
              padding: '4px 8px',
              backgroundColor: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              fontSize: '11px',
              cursor: 'pointer'
            }}
          >
            清除所有记录
          </button>
        </div>
      </div>
      
      {/* Event List */}
      <div style={{ 
        height: 'calc(100vh - 250px)', 
        overflowY: 'auto',
        backgroundColor: '#222',
        borderRadius: '5px',
        padding: '5px'
      }}>
        {loading ? (
          <div style={{ color: '#ccc', textAlign: 'center', padding: '20px' }}>
            加载中...
          </div>
        ) : events.length === 0 ? (
          <div style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
            暂无事件记录
          </div>
        ) : (
          events.map((event, index) => (
            <div
              key={event.id}
              style={{
                padding: '8px',
                marginBottom: '2px',
                backgroundColor: index % 2 === 0 ? '#2a2a2a' : '#333',
                borderLeft: `3px solid ${getEventTypeColor(event.event_type)}`,
                fontSize: '11px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ color: '#fff', fontWeight: 'bold' }}>
                    Day {event.day}h{event.hour}m{event.minute} | {event.agent_name}
                  </div>
                  
                  <div style={{ color: '#ccc', marginTop: '2px' }}>
                    {event.description}
                  </div>
                  
                  {event.details && (
                    <div style={{ color: '#888', marginTop: '2px', fontSize: '10px' }}>
                      详情: {event.details}
                    </div>
                  )}
                </div>
                
                <div style={{
                  padding: '2px 6px',
                  backgroundColor: getEventTypeColor(event.event_type),
                  color: 'white',
                  borderRadius: '3px',
                  fontSize: '10px',
                  marginLeft: '10px'
                }}>
                  {event.event_type}
                </div>
              </div>
              
              <div style={{ color: '#666', fontSize: '10px', marginTop: '4px' }}>
                记录时间: {event.timestamp}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default EventLogPanel;