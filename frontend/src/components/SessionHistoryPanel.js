/**
 * Session History Panel - 历史会话管理面板
 * 显示所有历史会话并提供下载功能
 */
import React, { useState, useEffect } from 'react';

function SessionHistoryPanel() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedSessions, setSelectedSessions] = useState(new Set());
  const [sortBy, setSortBy] = useState('start_time');
  const [sortOrder, setSortOrder] = useState('desc');
  const [filterText, setFilterText] = useState('');
  const [downloadingSession, setDownloadingSession] = useState(null);

  // Load sessions on component mount
  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:24861/api/v1/sessions');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const sessionsData = await response.json();
      setSessions(sessionsData || []);
    } catch (err) {
      console.error('Error loading sessions:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Download functions
  const downloadSessionData = async (sessionId, format, dataType = 'events') => {
    setDownloadingSession(sessionId);
    try {
      let endpoint = '';
      if (dataType === 'ai_decisions') {
        endpoint = `http://localhost:24861/api/v1/events/export/ai_decisions?session_id=${sessionId}`;
      } else {
        endpoint = `http://localhost:24861/api/v1/events/export/${format}?session_id=${sessionId}`;
      }

      const response = await fetch(endpoint);
      if (!response.ok) {
        throw new Error(`下载失败: ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Extract filename from response headers or create a default one
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `${sessionId}_${dataType}.${format}`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=([^;]+)/);
        if (filenameMatch) {
          filename = filenameMatch[1].replace(/"/g, '');
        }
      }
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download error:', err);
      alert(`下载失败: ${err.message}`);
    } finally {
      setDownloadingSession(null);
    }
  };

  const downloadSessionSummary = async (sessionId) => {
    setDownloadingSession(sessionId);
    try {
      const response = await fetch(`http://localhost:24861/api/v1/sessions/${sessionId}/summary`);
      if (!response.ok) {
        throw new Error(`获取会话摘要失败: ${response.statusText}`);
      }
      
      const data = await response.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${sessionId}_summary.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Summary download error:', err);
      alert(`下载摘要失败: ${err.message}`);
    } finally {
      setDownloadingSession(null);
    }
  };

  // Batch download for selected sessions
  const downloadSelectedSessions = async (format, dataType = 'events') => {
    if (selectedSessions.size === 0) {
      alert('请先选择要下载的会话');
      return;
    }

    for (const sessionId of selectedSessions) {
      await downloadSessionData(sessionId, format, dataType);
      // Add small delay between downloads
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  };

  // Filter and sort sessions
  const getFilteredAndSortedSessions = () => {
    let filtered = sessions;
    
    // Apply text filter
    if (filterText) {
      filtered = sessions.filter(session => 
        session.session_id.toLowerCase().includes(filterText.toLowerCase()) ||
        session.agents.some(agent => agent.toLowerCase().includes(filterText.toLowerCase()))
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];
      
      if (sortBy === 'start_time' || sortBy === 'end_time') {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  };

  const toggleSessionSelection = (sessionId) => {
    const newSelected = new Set(selectedSessions);
    if (newSelected.has(sessionId)) {
      newSelected.delete(sessionId);
    } else {
      newSelected.add(sessionId);
    }
    setSelectedSessions(newSelected);
  };

  const selectAllSessions = () => {
    const filtered = getFilteredAndSortedSessions();
    setSelectedSessions(new Set(filtered.map(s => s.session_id)));
  };

  const clearSelection = () => {
    setSelectedSessions(new Set());
  };

  const formatDateTime = (dateTimeStr) => {
    try {
      return new Date(dateTimeStr).toLocaleString('zh-CN');
    } catch {
      return dateTimeStr;
    }
  };

  const calculateDuration = (startTime, endTime) => {
    try {
      const start = new Date(startTime);
      const end = new Date(endTime);
      const diffMs = end - start;
      const diffMins = Math.floor(diffMs / 60000);
      const hours = Math.floor(diffMins / 60);
      const mins = diffMins % 60;
      return hours > 0 ? `${hours}小时${mins}分钟` : `${mins}分钟`;
    } catch {
      return '-';
    }
  };

  const filteredSessions = getFilteredAndSortedSessions();

  return (
    <div className="panel" style={{ 
      height: '100%', 
      overflow: 'hidden',
      padding: '20px',
      backgroundColor: '#1a1a1a',
      color: 'white'
    }}>
      <h2 style={{ marginTop: '10px', color: '#fff' }}>📚 历史会话管理</h2>
      
      {/* Header Controls */}
      <div style={{ marginBottom: '15px' }}>
        {/* Filter and Sort Controls */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '10px', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="搜索会话ID或Agent名称..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            style={{
              flex: 1,
              minWidth: '200px',
              padding: '5px',
              backgroundColor: '#333',
              color: 'white',
              border: '1px solid #555',
              borderRadius: '3px',
              fontSize: '11px'
            }}
          />
          
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{
              padding: '5px',
              backgroundColor: '#333',
              color: 'white',
              border: '1px solid #555',
              borderRadius: '3px',
              fontSize: '11px'
            }}
          >
            <option value="start_time">按开始时间</option>
            <option value="end_time">按结束时间</option>
            <option value="event_count">按事件数量</option>
            <option value="days_count">按持续天数</option>
          </select>
          
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            style={{
              padding: '5px 10px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              fontSize: '11px',
              cursor: 'pointer'
            }}
          >
            {sortOrder === 'asc' ? '↑ 升序' : '↓ 降序'}
          </button>
          
          <button
            onClick={loadSessions}
            disabled={loading}
            style={{
              padding: '5px 10px',
              backgroundColor: loading ? '#666' : '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              fontSize: '11px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? '刷新中...' : '🔄 刷新'}
          </button>
        </div>

        {/* Batch Operations */}
        <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '11px', color: '#ccc' }}>
            选中 {selectedSessions.size} / {filteredSessions.length} 个会话
          </span>
          
          <button
            onClick={selectAllSessions}
            style={{
              padding: '4px 8px',
              backgroundColor: '#FF9800',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              fontSize: '10px',
              cursor: 'pointer'
            }}
          >
            全选
          </button>
          
          <button
            onClick={clearSelection}
            style={{
              padding: '4px 8px',
              backgroundColor: '#666',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              fontSize: '10px',
              cursor: 'pointer'
            }}
          >
            清空
          </button>
          
          {selectedSessions.size > 0 && (
            <>
              <button
                onClick={() => downloadSelectedSessions('csv')}
                style={{
                  padding: '4px 8px',
                  backgroundColor: '#2196F3',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  fontSize: '10px',
                  cursor: 'pointer'
                }}
              >
                批量下载CSV
              </button>
              
              <button
                onClick={() => downloadSelectedSessions('csv', 'ai_decisions')}
                style={{
                  padding: '4px 8px',
                  backgroundColor: '#9C27B0',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  fontSize: '10px',
                  cursor: 'pointer'
                }}
              >
                批量下载AI数据
              </button>
            </>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          padding: '10px',
          backgroundColor: '#f44336',
          color: 'white',
          borderRadius: '4px',
          marginBottom: '15px',
          fontSize: '12px'
        }}>
          ❌ 加载失败: {error}
        </div>
      )}

      {/* Sessions Table */}
      <div style={{ 
        height: 'calc(100% - 200px)', 
        overflowY: 'auto',
        backgroundColor: '#222',
        borderRadius: '5px'
      }}>
        {loading ? (
          <div style={{ 
            padding: '40px', 
            textAlign: 'center', 
            color: '#ccc',
            fontSize: '14px'
          }}>
            🔄 加载会话数据中...
          </div>
        ) : filteredSessions.length === 0 ? (
          <div style={{ 
            padding: '40px', 
            textAlign: 'center', 
            color: '#666',
            fontSize: '14px'
          }}>
            {filterText ? '没有找到匹配的会话' : '暂无历史会话'}
          </div>
        ) : (
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            fontSize: '11px'
          }}>
            <thead>
              <tr style={{ 
                backgroundColor: '#333',
                position: 'sticky',
                top: 0,
                zIndex: 1
              }}>
                <th style={{ padding: '8px', textAlign: 'center', width: '30px' }}>选择</th>
                <th style={{ padding: '8px', textAlign: 'left' }}>会话ID</th>
                <th style={{ padding: '8px', textAlign: 'center' }}>开始时间</th>
                <th style={{ padding: '8px', textAlign: 'center' }}>持续时间</th>
                <th style={{ padding: '8px', textAlign: 'center' }}>事件数</th>
                <th style={{ padding: '8px', textAlign: 'center' }}>Agent数</th>
                <th style={{ padding: '8px', textAlign: 'center' }}>天数</th>
                <th style={{ padding: '8px', textAlign: 'left' }}>参与Agent</th>
                <th style={{ padding: '8px', textAlign: 'center' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredSessions.map((session, index) => (
                <tr 
                  key={session.session_id}
                  style={{
                    backgroundColor: index % 2 === 0 ? '#2a2a2a' : '#333',
                    borderBottom: '1px solid #444'
                  }}
                >
                  <td style={{ padding: '8px', textAlign: 'center' }}>
                    <input
                      type="checkbox"
                      checked={selectedSessions.has(session.session_id)}
                      onChange={() => toggleSessionSelection(session.session_id)}
                      style={{ transform: 'scale(0.8)' }}
                    />
                  </td>
                  
                  <td style={{ 
                    padding: '8px',
                    fontFamily: 'monospace',
                    color: '#fff',
                    fontWeight: 'bold'
                  }}>
                    {session.session_id}
                  </td>
                  
                  <td style={{ padding: '8px', textAlign: 'center', color: '#ccc' }}>
                    {formatDateTime(session.start_time)}
                  </td>
                  
                  <td style={{ padding: '8px', textAlign: 'center', color: '#ccc' }}>
                    {calculateDuration(session.start_time, session.end_time)}
                  </td>
                  
                  <td style={{ 
                    padding: '8px', 
                    textAlign: 'center',
                    color: session.event_count > 50 ? '#4CAF50' : '#ccc'
                  }}>
                    {session.event_count}
                  </td>
                  
                  <td style={{ padding: '8px', textAlign: 'center', color: '#ccc' }}>
                    {session.agent_count}
                  </td>
                  
                  <td style={{ padding: '8px', textAlign: 'center', color: '#ccc' }}>
                    {session.days_count}
                  </td>
                  
                  <td style={{ padding: '8px', color: '#ccc' }}>
                    {session.agents.slice(0, 3).join(', ')}
                    {session.agents.length > 3 && '...'}
                  </td>
                  
                  <td style={{ padding: '8px' }}>
                    <div style={{ display: 'flex', gap: '3px', flexWrap: 'wrap' }}>
                      <button
                        onClick={() => downloadSessionData(session.session_id, 'csv')}
                        disabled={downloadingSession === session.session_id}
                        style={{
                          padding: '3px 6px',
                          backgroundColor: '#2196F3',
                          color: 'white',
                          border: 'none',
                          borderRadius: '2px',
                          fontSize: '9px',
                          cursor: 'pointer'
                        }}
                        title="下载完整CSV数据"
                      >
                        CSV
                      </button>
                      
                      <button
                        onClick={() => downloadSessionData(session.session_id, 'json')}
                        disabled={downloadingSession === session.session_id}
                        style={{
                          padding: '3px 6px',
                          backgroundColor: '#4CAF50',
                          color: 'white',
                          border: 'none',
                          borderRadius: '2px',
                          fontSize: '9px',
                          cursor: 'pointer'
                        }}
                        title="下载JSON数据"
                      >
                        JSON
                      </button>
                      
                      <button
                        onClick={() => downloadSessionData(session.session_id, 'csv', 'ai_decisions')}
                        disabled={downloadingSession === session.session_id}
                        style={{
                          padding: '3px 6px',
                          backgroundColor: '#9C27B0',
                          color: 'white',
                          border: 'none',
                          borderRadius: '2px',
                          fontSize: '9px',
                          cursor: 'pointer'
                        }}
                        title="下载AI决策数据"
                      >
                        AI
                      </button>
                      
                      <button
                        onClick={() => downloadSessionSummary(session.session_id)}
                        disabled={downloadingSession === session.session_id}
                        style={{
                          padding: '3px 6px',
                          backgroundColor: '#FF9800',
                          color: 'white',
                          border: 'none',
                          borderRadius: '2px',
                          fontSize: '9px',
                          cursor: 'pointer'
                        }}
                        title="下载会话摘要"
                      >
                        摘要
                      </button>
                    </div>
                    
                    {downloadingSession === session.session_id && (
                      <div style={{ 
                        fontSize: '8px', 
                        color: '#4CAF50',
                        marginTop: '2px'
                      }}>
                        下载中...
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer Stats */}
      <div style={{
        marginTop: '10px',
        padding: '8px',
        backgroundColor: '#333',
        borderRadius: '3px',
        fontSize: '10px',
        color: '#ccc',
        display: 'flex',
        justifyContent: 'space-between'
      }}>
        <span>
          总计: {sessions.length} 个会话 | 显示: {filteredSessions.length} 个
        </span>
        <span>
          总事件数: {sessions.reduce((sum, s) => sum + s.event_count, 0)}
        </span>
      </div>
    </div>
  );
}

export default SessionHistoryPanel;