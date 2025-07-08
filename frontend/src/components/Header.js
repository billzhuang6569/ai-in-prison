/**
 * Header component for Project Prometheus
 */
import React from 'react';
import useWorldStore from '../store/worldStore';

function Header({ onSessionHistoryClick }) {
  const { worldState } = useWorldStore();
  
  return (
    <header style={{
      backgroundColor: '#333',
      color: '#fff',
      padding: '10px 20px',
      borderBottom: '1px solid #444',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }}>
      <h1 style={{ margin: 0, fontSize: '20px' }}>
        Project Prometheus (普罗米修斯计划)
      </h1>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
        <button
          onClick={onSessionHistoryClick}
          style={{
            padding: '6px 12px',
            backgroundColor: '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '12px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}
          title="查看和管理历史会话"
        >
          📚 历史会话
        </button>
        
        {worldState && (
          <div style={{ fontSize: '14px', color: '#ccc' }}>
            {worldState.is_running ? '实验运行中' : '实验已停止'} - 
            第 {worldState.day} 天, 第 {worldState.hour} 小时
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;