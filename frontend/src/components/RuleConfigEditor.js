/**
 * Rule Configuration Editor - 规则配置编辑器
 * 支持动态配置现有规则和添加新规则
 */
import React, { useState, useEffect } from 'react';

const API_BASE = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:24861';

function RuleConfigEditor({ ruleId, onClose, onUpdate }) {
  const [config, setConfig] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [ruleSchema, setRuleSchema] = useState(null);

  // 规则模板定义 - 支持未来扩展
  const ruleTemplates = {
    temporal: {
      name: "时间规则",
      description: "基于时间触发的规则",
      parameters: {
        trigger_hours: { type: "array", label: "触发小时", default: [8, 12, 16, 20] },
        priority: { type: "number", label: "优先级", default: 5, min: 1, max: 10 },
        enabled: { type: "boolean", label: "启用", default: true }
      }
    },
    resource: {
      name: "资源规则",
      description: "管理游戏内资源的规则",
      parameters: {
        resource_type: { type: "select", label: "资源类型", options: ["food", "water", "items"], default: "food" },
        scarcity_factor: { type: "number", label: "稀缺因子", default: 0.8, min: 0.1, max: 1.0, step: 0.1 },
        priority: { type: "number", label: "优先级", default: 5, min: 1, max: 10 },
        enabled: { type: "boolean", label: "启用", default: true }
      }
    },
    behavior: {
      name: "行为规则",
      description: "控制AI行为的规则",
      parameters: {
        behavior_type: { type: "select", label: "行为类型", options: ["aggression", "cooperation", "exploration"], default: "cooperation" },
        intensity: { type: "number", label: "强度", default: 1.0, min: 0.1, max: 2.0, step: 0.1 },
        priority: { type: "number", label: "优先级", default: 5, min: 1, max: 10 },
        enabled: { type: "boolean", label: "启用", default: true }
      }
    },
    environmental: {
      name: "环境规则",
      description: "控制环境变化的规则",
      parameters: {
        event_type: { type: "select", label: "事件类型", options: ["weather", "emergency", "maintenance"], default: "weather" },
        frequency: { type: "number", label: "频率(小时)", default: 24, min: 1, max: 168 },
        priority: { type: "number", label: "优先级", default: 5, min: 1, max: 10 },
        enabled: { type: "boolean", label: "启用", default: true }
      }
    },
    social: {
      name: "社交规则",
      description: "控制社交互动的规则",
      parameters: {
        interaction_type: { type: "select", label: "互动类型", options: ["conversation", "alliance", "conflict"], default: "conversation" },
        boost_factor: { type: "number", label: "增强因子", default: 1.0, min: 0.1, max: 3.0, step: 0.1 },
        priority: { type: "number", label: "优先级", default: 5, min: 1, max: 10 },
        enabled: { type: "boolean", label: "启用", default: true }
      }
    }
  };

  // 特定规则的配置模板
  const specificRuleConfigs = {
    guard_food_distribution: {
      name: "狱警食物分发",
      category: "temporal",
      parameters: {
        schedule: { type: "array", label: "分发时间", default: [8, 12, 16, 20] },
        food_per_guard: { type: "number", label: "每个狱警食物数", default: 2, min: 1, max: 10 },
        water_per_guard: { type: "number", label: "每个狱警水数", default: 2, min: 1, max: 10 },
        priority: { type: "number", label: "优先级", default: 8, min: 1, max: 10 },
        enabled: { type: "boolean", label: "启用", default: true }
      }
    },
    cafeteria_food_supply: {
      name: "食堂食物供应",
      category: "temporal",
      parameters: {
        meal_times: { type: "array", label: "用餐时间", default: [7, 12, 15, 18, 21] },
        scarcity_factor: { type: "number", label: "稀缺因子", default: 0.8, min: 0.1, max: 1.0, step: 0.1 },
        competition_enabled: { type: "boolean", label: "启用竞争", default: true },
        priority: { type: "number", label: "优先级", default: 9, min: 1, max: 10 },
        enabled: { type: "boolean", label: "启用", default: true }
      }
    },
    food_scarcity: {
      name: "食物稀缺性",
      category: "resource",
      parameters: {
        high_demand_threshold: { type: "number", label: "高需求阈值", default: 3, min: 1, max: 10 },
        competition_boost: { type: "number", label: "竞争增强", default: 1.5, min: 1.0, max: 3.0, step: 0.1 },
        hoarding_prevention: { type: "boolean", label: "防止囤积", default: true },
        priority: { type: "number", label: "优先级", default: 6, min: 1, max: 10 },
        enabled: { type: "boolean", label: "启用", default: true }
      }
    }
  };

  useEffect(() => {
    loadRuleConfig();
  }, [ruleId]);

  const loadRuleConfig = async () => {
    setLoading(true);
    try {
      // 尝试获取现有规则配置
      if (ruleId) {
        // 对于现有规则，使用特定配置或默认模板
        const schema = specificRuleConfigs[ruleId] || {
          name: ruleId,
          category: "temporal",
          parameters: ruleTemplates.temporal.parameters
        };
        setRuleSchema(schema);
        
        // 设置默认配置值
        const defaultConfig = {};
        Object.entries(schema.parameters).forEach(([key, param]) => {
          defaultConfig[key] = param.default;
        });
        setConfig(defaultConfig);
      }
    } catch (err) {
      setError('Failed to load rule configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (key, value) => {
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // 这里将来可以调用API保存配置
      const response = await fetch(`${API_BASE}/rules/food-distribution/configure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          rule_id: ruleId,
          config: config
        })
      });

      const data = await response.json();
      if (data.success) {
        onUpdate && onUpdate(ruleId, config);
        onClose();
      } else {
        setError(data.message || 'Failed to save configuration');
      }
    } catch (err) {
      setError('Error saving configuration: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const renderParameterInput = (key, param) => {
    const value = config[key];

    switch (param.type) {
      case 'boolean':
        return (
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={value || false}
              onChange={(e) => handleConfigChange(key, e.target.checked)}
            />
            <span className="checkbox-text">{param.label}</span>
          </label>
        );

      case 'number':
        return (
          <div className="number-input">
            <label>{param.label}:</label>
            <input
              type="number"
              value={value || param.default}
              min={param.min}
              max={param.max}
              step={param.step || 1}
              onChange={(e) => handleConfigChange(key, parseFloat(e.target.value))}
            />
          </div>
        );

      case 'select':
        return (
          <div className="select-input">
            <label>{param.label}:</label>
            <select
              value={value || param.default}
              onChange={(e) => handleConfigChange(key, e.target.value)}
            >
              {param.options.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </div>
        );

      case 'array':
        const arrayValue = Array.isArray(value) ? value.join(', ') : '';
        return (
          <div className="array-input">
            <label>{param.label}:</label>
            <input
              type="text"
              placeholder="用逗号分隔，如: 8, 12, 16, 20"
              value={arrayValue}
              onChange={(e) => {
                const newArray = e.target.value.split(',').map(v => parseInt(v.trim())).filter(v => !isNaN(v));
                handleConfigChange(key, newArray);
              }}
            />
          </div>
        );

      default:
        return (
          <div className="text-input">
            <label>{param.label}:</label>
            <input
              type="text"
              value={value || param.default || ''}
              onChange={(e) => handleConfigChange(key, e.target.value)}
            />
          </div>
        );
    }
  };

  if (loading) {
    return (
      <div className="rule-config-editor">
        <div className="editor-header">
          <h3>配置规则</h3>
          <button onClick={onClose}>×</button>
        </div>
        <div className="loading">正在加载配置...</div>
      </div>
    );
  }

  return (
    <div className="rule-config-editor">
      <div className="editor-header">
        <h3>配置规则: {ruleSchema?.name || ruleId}</h3>
        <button onClick={onClose}>×</button>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      <div className="editor-content">
        {ruleSchema && (
          <>
            <div className="rule-info">
              <p className="rule-description">{ruleSchema.description || '配置此规则的参数'}</p>
              <p className="rule-category">分类: {ruleSchema.category}</p>
            </div>

            <div className="parameters-section">
              <h4>参数设置:</h4>
              <div className="parameters-grid">
                {Object.entries(ruleSchema.parameters).map(([key, param]) => (
                  <div key={key} className="parameter-item">
                    {renderParameterInput(key, param)}
                  </div>
                ))}
              </div>
            </div>

            <div className="preview-section">
              <h4>配置预览:</h4>
              <pre className="config-preview">
                {JSON.stringify(config, null, 2)}
              </pre>
            </div>
          </>
        )}
      </div>

      <div className="editor-footer">
        <button onClick={onClose} className="cancel-btn">
          取消
        </button>
        <button 
          onClick={handleSave} 
          className="save-btn"
          disabled={saving}
        >
          {saving ? '保存中...' : '保存配置'}
        </button>
      </div>

      <style jsx>{`
        .rule-config-editor {
          background: white;
          border: 1px solid #ccc;
          border-radius: 8px;
          width: 600px;
          max-height: 80vh;
          overflow-y: auto;
          font-family: monospace;
          font-size: 12px;
        }

        .editor-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          background: #f5f5f5;
          border-bottom: 1px solid #ddd;
          border-radius: 7px 7px 0 0;
        }

        .editor-header h3 {
          margin: 0;
          font-size: 14px;
        }

        .editor-header button {
          background: #ff4444;
          color: white;
          border: none;
          border-radius: 50%;
          width: 24px;
          height: 24px;
          cursor: pointer;
          font-weight: bold;
        }

        .error-message {
          background: #ffeeee;
          color: #cc0000;
          padding: 8px 16px;
          border-bottom: 1px solid #ffcccc;
        }

        .loading {
          padding: 40px;
          text-align: center;
          color: #666;
        }

        .editor-content {
          padding: 16px;
        }

        .rule-info {
          margin-bottom: 20px;
          padding: 12px;
          background: #f8f9fa;
          border-radius: 4px;
        }

        .rule-description {
          margin: 0 0 8px 0;
          color: #666;
        }

        .rule-category {
          margin: 0;
          font-weight: bold;
          color: #007bff;
        }

        .parameters-section h4 {
          margin: 0 0 12px 0;
          color: #333;
        }

        .parameters-grid {
          display: grid;
          gap: 12px;
        }

        .parameter-item {
          padding: 8px;
          border: 1px solid #e0e0e0;
          border-radius: 4px;
        }

        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
        }

        .checkbox-text {
          font-weight: bold;
        }

        .number-input, .select-input, .array-input, .text-input {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
        }

        .number-input label, .select-input label, .array-input label, .text-input label {
          font-weight: bold;
          min-width: 120px;
        }

        .number-input input, .select-input select, .array-input input, .text-input input {
          flex: 1;
          padding: 4px 8px;
          border: 1px solid #ccc;
          border-radius: 3px;
          font-family: monospace;
          font-size: 11px;
        }

        .preview-section {
          margin-top: 20px;
        }

        .preview-section h4 {
          margin: 0 0 8px 0;
          color: #333;
        }

        .config-preview {
          background: #f8f9fa;
          border: 1px solid #e0e0e0;
          border-radius: 4px;
          padding: 12px;
          font-size: 10px;
          overflow-x: auto;
          white-space: pre-wrap;
        }

        .editor-footer {
          display: flex;
          justify-content: flex-end;
          gap: 8px;
          padding: 12px 16px;
          background: #f5f5f5;
          border-top: 1px solid #ddd;
          border-radius: 0 0 7px 7px;
        }

        .cancel-btn, .save-btn {
          padding: 6px 12px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-family: monospace;
          font-size: 11px;
        }

        .cancel-btn {
          background: #6c757d;
          color: white;
        }

        .save-btn {
          background: #28a745;
          color: white;
        }

        .save-btn:disabled {
          background: #6c757d;
          cursor: not-allowed;
        }

        .cancel-btn:hover {
          background: #545b62;
        }

        .save-btn:hover:not(:disabled) {
          background: #218838;
        }
      `}</style>
    </div>
  );
}

export default RuleConfigEditor;