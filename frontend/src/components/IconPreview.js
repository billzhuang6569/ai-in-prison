/**
 * Icon Preview Component - 图标预览测试组件
 * 用于验证Game Icons的选择是否合适
 */
import React from 'react';
import { Icon } from '@iconify/react';

const IconPreview = () => {
  // 所有使用的图标映射
  const iconGroups = {
    "道具工具栏": [
      { name: "展开箱子", icon: "game-icons:chest" },
      { name: "收起背包", icon: "game-icons:knapsack" }
    ],
    "基础物品": [
      { name: "食物", icon: "game-icons:meal" },
      { name: "饮水", icon: "game-icons:water-drop" },
      { name: "书籍", icon: "game-icons:book-cover" }
    ],
    "狱警装备": [
      { name: "警棍", icon: "game-icons:truncheon" },
      { name: "手铐", icon: "game-icons:handcuffed" },
      { name: "对讲机", icon: "game-icons:radio-tower" },
      { name: "钥匙", icon: "game-icons:key" },
      { name: "急救包", icon: "game-icons:first-aid-kit" },
      { name: "哨子", icon: "game-icons:whistle" }
    ],
    "囚犯物品": [
      { name: "香烟", icon: "game-icons:cigarette" },
      { name: "扑克牌", icon: "game-icons:card-play" },
      { name: "日记本", icon: "game-icons:notebook" },
      { name: "铁勺", icon: "game-icons:spoon" },
      { name: "床单", icon: "game-icons:bed" },
      { name: "肥皂", icon: "game-icons:soap" }
    ],
    "制造物品": [
      { name: "简易刀具", icon: "game-icons:switchblade" },
      { name: "绳子", icon: "game-icons:rope-coil" },
      { name: "撬锁工具", icon: "game-icons:lock-picks" },
      { name: "工具箱", icon: "game-icons:toolbox" }
    ],
    "环境物品": [
      { name: "椅子", icon: "game-icons:chair" },
      { name: "桌子", icon: "game-icons:table" }
    ],
    "实验里程碑": [
      { name: "目标箭头", icon: "game-icons:target-arrows" },
      { name: "攻击事件", icon: "game-icons:crossed-swords" },
      { name: "对话事件", icon: "game-icons:conversation" },
      { name: "死亡事件", icon: "game-icons:skull" },
      { name: "规则宣布", icon: "game-icons:megaphone" },
      { name: "道具投放", icon: "game-icons:chest" },
      { name: "联盟形成", icon: "game-icons:handshake" },
      { name: "地道挖掘", icon: "game-icons:hole" },
      { name: "紧急集合", icon: "game-icons:siren" },
      { name: "偷窃事件", icon: "game-icons:stealing" },
      { name: "惩罚执行", icon: "game-icons:scales" }
    ],
    "占位符": [
      { name: "未知道具", icon: "game-icons:questioned-badge" }
    ]
  };

  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#1a1a1a', 
      color: 'white',
      minHeight: '100vh'
    }}>
      <h1>Game Icons 预览</h1>
      <p style={{ color: '#ccc', marginBottom: '30px' }}>
        Project Prometheus 中使用的所有 Game Icons 图标预览
      </p>

      {Object.entries(iconGroups).map(([groupName, icons]) => (
        <div key={groupName} style={{ marginBottom: '40px' }}>
          <h2 style={{ 
            borderBottom: '2px solid #444', 
            paddingBottom: '10px',
            marginBottom: '20px',
            color: '#4CAF50'
          }}>
            {groupName}
          </h2>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
            gap: '15px'
          }}>
            {icons.map((item) => (
              <div
                key={item.icon}
                style={{
                  padding: '15px',
                  backgroundColor: '#2a2a2a',
                  border: '1px solid #444',
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}
              >
                <Icon 
                  icon={item.icon} 
                  width="24" 
                  height="24" 
                  style={{ color: '#FFD700' }} 
                />
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                    {item.name}
                  </div>
                  <div style={{ fontSize: '11px', color: '#888', marginTop: '2px' }}>
                    {item.icon}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div style={{ 
        marginTop: '40px', 
        padding: '20px', 
        backgroundColor: '#2a2a2a', 
        borderRadius: '8px',
        border: '1px solid #444'
      }}>
        <h3 style={{ color: '#4CAF50', marginBottom: '10px' }}>使用信息</h3>
        <ul style={{ color: '#ccc', lineHeight: '1.6' }}>
          <li><strong>图标库</strong>: @iconify-json/game-icons</li>
          <li><strong>图标总数</strong>: 4,123+ 游戏相关图标</li>
          <li><strong>许可证</strong>: CC BY 3.0</li>
          <li><strong>当前使用</strong>: {Object.values(iconGroups).flat().length} 个图标</li>
          <li><strong>React组件</strong>: @iconify/react</li>
        </ul>
      </div>
    </div>
  );
};

export default IconPreview;