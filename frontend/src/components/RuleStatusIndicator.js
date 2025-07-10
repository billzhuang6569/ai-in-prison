/**
 * Rule Status Indicator - 实时规则状态指示器
 * 显示在主界面上的小型规则状态指示器
 */
import React, { useState, useEffect } from 'react';

const API_BASE = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:24861';

function RuleStatusIndicator({ onClick }) {
  const [ruleStatus, setRuleStatus] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [isExpanded, setIsExpanded] = useState(false);

  // 获取规则状态
  const fetchRuleStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/rules/status`);
      const data = await response.json();
      if (data.success) {
        setRuleStatus(data.data);
      }
    } catch (err) {
      console.error('Failed to fetch rule status:', err);
    }
  };

  // 获取最近的规则执行事件
  const fetchRecentEvents = async () => {
    try {
      const response = await fetch(`${API_BASE}/rules/history?limit=5`);
      const data = await response.json();
      if (data.success) {
        setRecentEvents(data.data.history);
      }
    } catch (err) {
      console.error('Failed to fetch recent rule events:', err);
    }
  };

  useEffect(() => {
    fetchRuleStatus();
    fetchRecentEvents();

    // 定期更新状态
    const interval = setInterval(() => {
      fetchRuleStatus();
      fetchRecentEvents();
    }, 15000); // 每15秒更新

    return () => clearInterval(interval);
  }, []);

  if (!ruleStatus) {
    return (
      <div 
        className="rule-status-indicator loading"
        onClick={onClick}
        title="点击打开规则管理面板"
      >
        🔧 ⟳
      </div>
    );
  }

  const getStatusColor = () => {
    const ratio = ruleStatus.enabled_rules / ruleStatus.total_rules;
    if (ratio >= 0.8) return '#28a745'; // 绿色
    if (ratio >= 0.5) return '#ffc107'; // 黄色
    return '#dc3545'; // 红色
  };

  return (
    <div className="rule-status-indicator-container">
      <div 
        className="rule-status-indicator"
        onClick={() => setIsExpanded(!isExpanded)}
        style={{ backgroundColor: getStatusColor() }}
        title={`规则状态: ${ruleStatus.enabled_rules}/${ruleStatus.total_rules} 启用`}
      >
        🔧 {ruleStatus.enabled_rules}/{ruleStatus.total_rules}
      </div>

      {isExpanded && (
        <div className="rule-status-popup">
          <div className="popup-header">
            <span>规则引擎状态</span>
            <button onClick={() => setIsExpanded(false)}>×</button>
          </div>
          
          <div className="popup-content">
            <div className="status-summary">
              <div className="stat">
                <span className="label">总规则:</span>
                <span className="value">{ruleStatus.total_rules}</span>
              </div>
              <div className="stat">
                <span className="label">启用:</span>
                <span className="value enabled">{ruleStatus.enabled_rules}</span>
              </div>
            </div>

            <div className="categories-summary">
              <h4>分类状态:</h4>
              {Object.entries(ruleStatus.categories || {}).map(([category, count]) => (
                <div key={category} className="category-stat">
                  <span>{category}:</span>
                  <span>{count}</span>
                </div>
              ))}
            </div>

            {recentEvents.length > 0 && (
              <div className="recent-events">
                <h4>最近执行:</h4>
                {recentEvents.slice(0, 3).map((event, index) => (
                  <div key={index} className="event-item">
                    <span className="event-time">{event.timestamp}</span>
                    <span className="event-rule">{event.rule_id}</span>
                  </div>
                ))}
              </div>
            )}

            <button className="open-panel-btn" onClick={onClick}>
              打开规则管理面板
            </button>
          </div>
        </div>
      )}

      <style jsx>{`
        .rule-status-indicator-container {
          position: relative;
        }

        .rule-status-indicator {
          position: fixed;
          bottom: 20px;
          right: 20px;
          background: #007bff;
          color: white;
          padding: 8px 12px;
          border-radius: 20px;
          cursor: pointer;
          font-family: monospace;
          font-size: 12px;
          font-weight: bold;
          z-index: 100;
          border: 2px solid rgba(255, 255, 255, 0.3);
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
          transition: all 0.3s ease;
        }

        .rule-status-indicator:hover {
          transform: scale(1.05);
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        }

        .rule-status-indicator.loading {
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }

        .rule-status-popup {
          position: fixed;
          bottom: 70px;
          right: 20px;
          background: white;
          border: 1px solid #ccc;
          border-radius: 8px;
          width: 280px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
          z-index: 101;
          font-family: monospace;
          font-size: 12px;
        }

        .popup-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 12px;
          background: #f5f5f5;
          border-bottom: 1px solid #ddd;
          border-radius: 7px 7px 0 0;
          font-weight: bold;
        }

        .popup-header button {
          background: none;
          border: none;
          font-size: 16px;
          cursor: pointer;
          color: #666;
        }

        .popup-content {
          padding: 12px;
        }

        .status-summary {
          display: flex;
          gap: 12px;
          margin-bottom: 12px;
        }

        .stat {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2px;
        }

        .stat .label {
          color: #666;
          font-size: 10px;
        }

        .stat .value {
          font-weight: bold;
          font-size: 14px;
        }

        .stat .value.enabled {
          color: #28a745;
        }

        .categories-summary {
          margin-bottom: 12px;
        }

        .categories-summary h4 {
          margin: 0 0 6px 0;
          font-size: 11px;
          color: #666;
        }

        .category-stat {
          display: flex;
          justify-content: space-between;
          font-size: 10px;
          margin-bottom: 2px;
        }

        .recent-events {
          margin-bottom: 12px;
        }

        .recent-events h4 {
          margin: 0 0 6px 0;
          font-size: 11px;
          color: #666;
        }

        .event-item {
          display: flex;
          justify-content: space-between;
          font-size: 9px;
          margin-bottom: 2px;
          color: #888;
        }

        .event-time {
          color: #666;
        }

        .event-rule {
          font-weight: bold;
        }

        .open-panel-btn {
          width: 100%;
          padding: 6px;
          background: #007bff;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-family: monospace;
          font-size: 11px;
        }

        .open-panel-btn:hover {
          background: #0056b3;
        }
      `}</style>
    </div>
  );
}

export default RuleStatusIndicator;