/**
 * Rule Management Panel - 规则管理面板
 * 管理所有实验规则的启用/禁用、配置和监控
 */
import React, { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:24861';

function RuleManagementPanel({ onClose }) {
  const [rules, setRules] = useState([]);
  const [ruleStatus, setRuleStatus] = useState({});
  const [ruleHistory, setRuleHistory] = useState([]);
  const [categories, setCategories] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [foodDistributionStatus, setFoodDistributionStatus] = useState({});
  const [nextTriggers, setNextTriggers] = useState([]);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // 获取规则状态
  const fetchRuleStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/rules/status`);
      const data = await response.json();
      if (data.success) {
        setRuleStatus(data.data);
      }
    } catch (err) {
      console.error('Failed to fetch rule status:', err);
    }
  }, []);

  // 获取规则列表
  const fetchRules = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/rules/list`);
      const data = await response.json();
      // 确保data是数组
      if (Array.isArray(data)) {
        setRules(data);
      } else {
        console.error('Rules data is not an array:', data);
        setRules([]);
        setError('Invalid rules data format');
      }
    } catch (err) {
      console.error('Failed to fetch rules:', err);
      setRules([]); // 确保rules始终是数组
      setError('Failed to load rules');
    }
  }, []);

  // 获取规则分类
  const fetchCategories = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/rules/categories`);
      const data = await response.json();
      if (data.success) {
        setCategories(data.data);
      }
    } catch (err) {
      console.error('Failed to fetch categories:', err);
    }
  }, []);

  // 获取执行历史
  const fetchHistory = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/rules/history?limit=20`);
      const data = await response.json();
      if (data.success) {
        setRuleHistory(data.data.history);
      }
    } catch (err) {
      console.error('Failed to fetch rule history:', err);
    }
  }, []);

  // 获取食物分发状态
  const fetchFoodDistributionStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/rules/food-distribution/status`);
      const data = await response.json();
      if (data.success) {
        setFoodDistributionStatus(data.data);
      }
    } catch (err) {
      console.error('Failed to fetch food distribution status:', err);
    }
  }, []);

  // 获取下次触发时间
  const fetchNextTriggers = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/rules/debug/next-triggers`);
      const data = await response.json();
      if (data.success) {
        setNextTriggers(data.data.next_triggers);
      }
    } catch (err) {
      console.error('Failed to fetch next triggers:', err);
    }
  }, []);

  // 启用规则
  const enableRule = async (ruleId) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/rules/enable/${ruleId}`, {
        method: 'POST'
      });
      const data = await response.json();
      if (data.success) {
        await fetchRules();
        await fetchRuleStatus();
      } else {
        setError(`Failed to enable rule: ${data.message}`);
      }
    } catch (err) {
      setError(`Error enabling rule: ${err.message}`);
    }
  };

  // 禁用规则
  const disableRule = async (ruleId) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/rules/disable/${ruleId}`, {
        method: 'POST'
      });
      const data = await response.json();
      if (data.success) {
        await fetchRules();
        await fetchRuleStatus();
      } else {
        setError(`Failed to disable rule: ${data.message}`);
      }
    } catch (err) {
      setError(`Error disabling rule: ${err.message}`);
    }
  };

  // 测试规则触发
  const testRule = async (ruleId) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/rules/test/${ruleId}`, {
        method: 'POST'
      });
      const data = await response.json();
      if (data.success) {
        const willTrigger = data.data.will_trigger ? '✅ 会触发' : '❌ 不会触发';
        alert(`规则测试结果:\n${willTrigger}\n当前时间: ${data.data.current_time}\n规则状态: ${data.data.rule_enabled ? '启用' : '禁用'}`);
      }
    } catch (err) {
      setError(`Error testing rule: ${err.message}`);
    }
  };

  // 初始化数据
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        await Promise.all([
          fetchRules(),
          fetchRuleStatus(),
          fetchCategories(),
          fetchHistory(),
          fetchFoodDistributionStatus(),
          fetchNextTriggers()
        ]);
      } catch (err) {
        setError('Failed to load rule management data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [fetchRules, fetchRuleStatus, fetchCategories, fetchHistory, fetchFoodDistributionStatus, fetchNextTriggers]);

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchRuleStatus();
      fetchHistory();
      fetchNextTriggers();
    }, 10000); // 每10秒刷新

    return () => clearInterval(interval);
  }, [autoRefresh, fetchRuleStatus, fetchHistory, fetchNextTriggers]);

  // 过滤规则
  const filteredRules = rules.filter(rule => {
    const matchesCategory = selectedCategory === 'all' || rule.category === selectedCategory;
    const matchesSearch = searchTerm === '' || 
      rule.rule_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rule.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  // 获取规则状态图标
  const getRuleStatusIcon = (rule) => {
    if (rule.enabled) {
      return <span className="status-enabled">🟢</span>;
    } else {
      return <span className="status-disabled">🔴</span>;
    }
  };

  // 获取分类图标
  const getCategoryIcon = (category) => {
    const icons = {
      temporal: '⏰',
      resource: '📦',
      behavior: '🤖',
      environmental: '🌍',
      social: '👥'
    };
    return icons[category] || '📋';
  };

  // 获取优先级颜色
  const getPriorityColor = (priority) => {
    if (priority >= 8) return '#ff4444';
    if (priority >= 6) return '#ff8800';
    if (priority >= 4) return '#ffaa00';
    return '#44aa44';
  };

  if (loading) {
    return (
      <div className="rule-management-panel">
        <div className="panel-header">
          <h2>🔧 规则管理</h2>
          <button onClick={onClose} className="close-btn">✕</button>
        </div>
        <div className="loading">正在加载规则数据...</div>
      </div>
    );
  }

  return (
    <div className="rule-management-panel">
      <div className="panel-header">
        <h2>🔧 规则管理面板</h2>
        <div className="header-controls">
          <label>
            <input 
              type="checkbox" 
              checked={autoRefresh} 
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            自动刷新
          </label>
          <button onClick={onClose} className="close-btn">✕</button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* 标签页导航 */}
      <div className="tab-navigation">
        <button 
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          📊 总览
        </button>
        <button 
          className={activeTab === 'rules' ? 'active' : ''}
          onClick={() => setActiveTab('rules')}
        >
          📋 规则管理
        </button>
        <button 
          className={activeTab === 'food' ? 'active' : ''}
          onClick={() => setActiveTab('food')}
        >
          🍽️ 食物分发
        </button>
        <button 
          className={activeTab === 'history' ? 'active' : ''}
          onClick={() => setActiveTab('history')}
        >
          📜 执行历史
        </button>
        <button 
          className={activeTab === 'schedule' ? 'active' : ''}
          onClick={() => setActiveTab('schedule')}
        >
          ⏰ 触发计划
        </button>
      </div>

      {/* 总览标签页 */}
      {activeTab === 'overview' && (
        <div className="tab-content">
          <div className="overview-stats">
            <div className="stat-card">
              <h3>规则统计</h3>
              <div className="stat-value">{ruleStatus.total_rules || 0}</div>
              <div className="stat-label">总规则数</div>
            </div>
            <div className="stat-card">
              <h3>启用规则</h3>
              <div className="stat-value enabled">{ruleStatus.enabled_rules || 0}</div>
              <div className="stat-label">活跃规则</div>
            </div>
            <div className="stat-card">
              <h3>最近执行</h3>
              <div className="stat-value">{ruleHistory.length}</div>
              <div className="stat-label">近期事件</div>
            </div>
          </div>

          <div className="categories-overview">
            <h3>📂 规则分类</h3>
            <div className="categories-grid">
              {Object.entries(categories).map(([category, info]) => (
                <div key={category} className="category-card">
                  <div className="category-icon">{getCategoryIcon(category)}</div>
                  <div className="category-name">{category}</div>
                  <div className="category-stats">
                    <span className="enabled-count">{info.enabled_rules}</span>
                    <span className="total-count">/ {info.total_rules}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 规则管理标签页 */}
      {activeTab === 'rules' && (
        <div className="tab-content">
          <div className="rules-controls">
            <div className="search-box">
              <input
                type="text"
                placeholder="搜索规则..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <option value="all">所有分类</option>
              {Object.keys(categories).map(category => (
                <option key={category} value={category}>
                  {getCategoryIcon(category)} {category}
                </option>
              ))}
            </select>
          </div>

          <div className="rules-list">
            {filteredRules.map(rule => (
              <div key={rule.rule_id} className="rule-item">
                <div className="rule-header">
                  <div className="rule-title">
                    {getRuleStatusIcon(rule)}
                    <span className="rule-name">{rule.rule_id}</span>
                    <span className="rule-category">
                      {getCategoryIcon(rule.category)} {rule.category}
                    </span>
                    <span 
                      className="rule-priority" 
                      style={{ color: getPriorityColor(rule.priority) }}
                    >
                      P{rule.priority}
                    </span>
                  </div>
                  <div className="rule-actions">
                    <button 
                      onClick={() => testRule(rule.rule_id)}
                      className="test-btn"
                      title="测试规则触发条件"
                    >
                      🧪 测试
                    </button>
                    {rule.enabled ? (
                      <button 
                        onClick={() => disableRule(rule.rule_id)}
                        className="disable-btn"
                      >
                        🔴 禁用
                      </button>
                    ) : (
                      <button 
                        onClick={() => enableRule(rule.rule_id)}
                        className="enable-btn"
                      >
                        🟢 启用
                      </button>
                    )}
                  </div>
                </div>
                <div className="rule-description">
                  {rule.description}
                </div>
                {rule.last_execution && (
                  <div className="rule-last-execution">
                    最后执行: {rule.last_execution}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 食物分发标签页 */}
      {activeTab === 'food' && (
        <div className="tab-content">
          <h3>🍽️ 食物分发规则状态</h3>
          <div className="food-distribution-grid">
            {Object.entries(foodDistributionStatus).map(([ruleId, status]) => (
              <div key={ruleId} className="food-rule-card">
                <h4>{ruleId.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
                {status.status === 'not_found' ? (
                  <div className="status-not-found">❌ 规则未找到</div>
                ) : (
                  <>
                    <div className={`status ${status.enabled ? 'enabled' : 'disabled'}`}>
                      {status.enabled ? '🟢 启用' : '🔴 禁用'}
                    </div>
                    <div className="priority">优先级: {status.priority}</div>
                    <div className="description">{status.description}</div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 执行历史标签页 */}
      {activeTab === 'history' && (
        <div className="tab-content">
          <h3>📜 规则执行历史</h3>
          <div className="history-list">
            {ruleHistory.map((record, index) => (
              <div key={index} className="history-item">
                <div className="history-time">{record.timestamp}</div>
                <div className="history-rule">
                  {getCategoryIcon(record.category)} {record.rule_id}
                </div>
                <div className="history-events">{record.events_count} 个事件</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 触发计划标签页 */}
      {activeTab === 'schedule' && (
        <div className="tab-content">
          <h3>⏰ 即将触发的规则</h3>
          <div className="schedule-list">
            {nextTriggers.map((trigger, index) => (
              <div key={index} className="schedule-item">
                <div className="schedule-time">
                  {trigger.trigger_time}
                  <span className="hours-from-now">
                    ({trigger.hours_from_now}小时后)
                  </span>
                </div>
                <div className="schedule-rule">
                  {getCategoryIcon(trigger.category)} {trigger.rule_id}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <style jsx>{`
        .rule-management-panel {
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 90vw;
          max-width: 900px;
          height: 80vh;
          background: white;
          border: 2px solid #333;
          border-radius: 8px;
          z-index: 1000;
          display: flex;
          flex-direction: column;
          font-family: monospace;
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          border-bottom: 1px solid #ccc;
          background: #f5f5f5;
          border-radius: 6px 6px 0 0;
        }

        .panel-header h2 {
          margin: 0;
          font-size: 18px;
        }

        .header-controls {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .close-btn {
          background: #ff4444;
          color: white;
          border: none;
          padding: 4px 8px;
          border-radius: 4px;
          cursor: pointer;
          font-weight: bold;
        }

        .close-btn:hover {
          background: #cc0000;
        }

        .error-message {
          background: #ffeeee;
          color: #cc0000;
          padding: 8px 12px;
          border-bottom: 1px solid #ffcccc;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .loading {
          padding: 40px;
          text-align: center;
          color: #666;
        }

        .tab-navigation {
          display: flex;
          border-bottom: 1px solid #ccc;
          background: #fafafa;
        }

        .tab-navigation button {
          padding: 10px 16px;
          border: none;
          background: none;
          cursor: pointer;
          border-bottom: 2px solid transparent;
          font-family: monospace;
        }

        .tab-navigation button:hover {
          background: #eee;
        }

        .tab-navigation button.active {
          background: white;
          border-bottom-color: #007bff;
          font-weight: bold;
        }

        .tab-content {
          flex: 1;
          padding: 16px;
          overflow-y: auto;
        }

        .overview-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 12px;
          margin-bottom: 20px;
        }

        .stat-card {
          background: #f8f9fa;
          padding: 12px;
          border-radius: 6px;
          text-align: center;
          border: 1px solid #dee2e6;
        }

        .stat-card h3 {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #666;
        }

        .stat-value {
          font-size: 24px;
          font-weight: bold;
          margin-bottom: 4px;
        }

        .stat-value.enabled {
          color: #28a745;
        }

        .stat-label {
          font-size: 12px;
          color: #888;
        }

        .categories-overview h3 {
          margin-bottom: 12px;
        }

        .categories-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
          gap: 8px;
        }

        .category-card {
          background: #f8f9fa;
          padding: 12px;
          border-radius: 6px;
          text-align: center;
          border: 1px solid #dee2e6;
        }

        .category-icon {
          font-size: 20px;
          margin-bottom: 4px;
        }

        .category-name {
          font-size: 12px;
          margin-bottom: 4px;
          font-weight: bold;
        }

        .category-stats {
          font-size: 11px;
          color: #666;
        }

        .enabled-count {
          color: #28a745;
          font-weight: bold;
        }

        .rules-controls {
          display: flex;
          gap: 12px;
          margin-bottom: 16px;
          align-items: center;
        }

        .search-box input {
          padding: 6px 10px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-family: monospace;
          min-width: 200px;
        }

        .rules-controls select {
          padding: 6px;
          border: 1px solid #ccc;
          border-radius: 4px;
          font-family: monospace;
        }

        .rules-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .rule-item {
          border: 1px solid #ddd;
          border-radius: 6px;
          padding: 12px;
          background: #fafafa;
        }

        .rule-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .rule-title {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .rule-name {
          font-weight: bold;
        }

        .rule-category {
          background: #e9ecef;
          padding: 2px 6px;
          border-radius: 3px;
          font-size: 11px;
        }

        .rule-priority {
          font-weight: bold;
          font-size: 12px;
        }

        .rule-actions {
          display: flex;
          gap: 6px;
        }

        .rule-actions button {
          padding: 4px 8px;
          border: none;
          border-radius: 3px;
          cursor: pointer;
          font-family: monospace;
          font-size: 11px;
        }

        .test-btn {
          background: #17a2b8;
          color: white;
        }

        .enable-btn {
          background: #28a745;
          color: white;
        }

        .disable-btn {
          background: #dc3545;
          color: white;
        }

        .rule-description {
          color: #666;
          font-size: 12px;
          line-height: 1.3;
        }

        .rule-last-execution {
          color: #888;
          font-size: 11px;
          margin-top: 4px;
        }

        .food-distribution-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 12px;
        }

        .food-rule-card {
          border: 1px solid #ddd;
          border-radius: 6px;
          padding: 12px;
          background: #fafafa;
        }

        .food-rule-card h4 {
          margin: 0 0 8px 0;
        }

        .status {
          margin-bottom: 4px;
          font-weight: bold;
        }

        .status.enabled {
          color: #28a745;
        }

        .status.disabled {
          color: #dc3545;
        }

        .status-not-found {
          color: #dc3545;
        }

        .priority {
          font-size: 12px;
          margin-bottom: 4px;
        }

        .description {
          color: #666;
          font-size: 11px;
          line-height: 1.3;
        }

        .history-list, .schedule-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .history-item, .schedule-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 12px;
          background: #f8f9fa;
          border-radius: 4px;
          border-left: 3px solid #007bff;
        }

        .history-time, .schedule-time {
          font-weight: bold;
          min-width: 120px;
          font-size: 12px;
        }

        .hours-from-now {
          color: #666;
          font-weight: normal;
          font-size: 11px;
        }

        .history-rule, .schedule-rule {
          flex: 1;
          font-family: monospace;
        }

        .history-events {
          color: #666;
          font-size: 11px;
        }

        .status-enabled {
          color: #28a745;
        }

        .status-disabled {
          color: #dc3545;
        }
      `}</style>
    </div>
  );
}

export default RuleManagementPanel;