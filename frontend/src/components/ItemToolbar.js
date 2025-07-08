/**
 * Item Toolbar Component for placing items on the map
 * 
 * Now using @iconify-json/game-icons for realistic game-style icons
 * 4,123+ game-related icons available
 * License: CC BY 3.0
 */
import React, { useState } from 'react';
import { Icon } from '@iconify/react';

const ItemToolbar = ({ onItemSelect, selectedItem, onClearSelection }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Available items organized by category with Game Icons
  const itemCategories = {
    "基础物品": [
      { id: "food", name: "食物", icon: "game-icons:meal", description: "基础食物，恢复饥饿值" },
      { id: "water", name: "饮水", icon: "game-icons:water-drop", description: "清洁饮用水，恢复渴度" },
      { id: "book", name: "书籍", icon: "game-icons:book-cover", description: "阅读材料，提升精神状态" }
    ],
    "狱警装备": [
      { id: "baton", name: "警棍", icon: "game-icons:truncheon", description: "执法工具，增强权威" },
      { id: "handcuffs", name: "手铐", icon: "game-icons:handcuffed", description: "约束工具" },
      { id: "radio", name: "对讲机", icon: "game-icons:radio-tower", description: "通讯设备" },
      { id: "keys", name: "钥匙", icon: "game-icons:key", description: "开启各区域的钥匙" },
      { id: "first_aid", name: "急救包", icon: "game-icons:first-aid-kit", description: "医疗用品" },
      { id: "whistle", name: "哨子", icon: "game-icons:whistle", description: "集合警报工具" }
    ],
    "囚犯物品": [
      { id: "cigarettes", name: "香烟", icon: "game-icons:cigarette", description: "交易货币和精神慰藉" },
      { id: "playing_cards", name: "扑克牌", icon: "game-icons:card-play", description: "娱乐工具，社交道具" },
      { id: "diary", name: "日记本", icon: "game-icons:notebook", description: "记录想法，缓解压力" },
      { id: "spoon", name: "铁勺", icon: "game-icons:spoon", description: "可作为挖掘工具" },
      { id: "bedsheet", name: "床单", icon: "game-icons:bed", description: "可制作绳子等工具" },
      { id: "soap", name: "肥皂", icon: "game-icons:soap", description: "清洁用品" }
    ],
    "制造物品": [
      { id: "shiv", name: "简易刀具", icon: "game-icons:switchblade", description: "危险的自制武器" },
      { id: "rope", name: "绳子", icon: "game-icons:rope-coil", description: "逃跑或攀爬工具" },
      { id: "lockpick", name: "撬锁工具", icon: "game-icons:lock-picks", description: "开锁工具" },
      { id: "toolbox", name: "工具箱", icon: "game-icons:toolbox", description: "包含各种工具" }
    ],
    "环境物品": [
      { id: "chair", name: "椅子", icon: "game-icons:chair", description: "可坐或作为武器" },
      { id: "table", name: "桌子", icon: "game-icons:table", description: "放置物品或掩护" }
    ]
  };

  const handleItemClick = (item) => {
    if (selectedItem?.id === item.id) {
      onClearSelection();
    } else {
      onItemSelect(item);
    }
  };

  return (
    <div 
      className="item-toolbar"
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        backgroundColor: '#2a2a2a',
        border: '1px solid #444',
        borderRadius: '8px',
        minWidth: isExpanded ? '400px' : '60px',
        maxHeight: isExpanded ? '400px' : '60px',
        overflow: 'hidden',
        transition: 'all 0.3s ease',
        zIndex: 100,
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
      }}
    >
      {/* Toggle Button */}
      <div 
        style={{
          height: '60px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          borderBottom: isExpanded ? '1px solid #444' : 'none',
          backgroundColor: selectedItem ? '#4CAF50' : '#2a2a2a',
          transition: 'background-color 0.3s ease'
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <Icon 
          icon={isExpanded ? "game-icons:chest" : "game-icons:knapsack"} 
          width="24" 
          height="24" 
          style={{ color: 'white' }} 
        />
        {isExpanded && (
          <span style={{ marginLeft: '10px', color: 'white', fontSize: '14px' }}>
            道具工具栏 {selectedItem && `(已选择: ${selectedItem.name})`}
          </span>
        )}
      </div>

      {/* Item Categories */}
      {isExpanded && (
        <div 
          style={{
            padding: '10px',
            overflowY: 'auto',
            maxHeight: '340px'
          }}
        >
          {selectedItem && (
            <div style={{ 
              marginBottom: '15px', 
              padding: '8px', 
              backgroundColor: '#4CAF50', 
              borderRadius: '4px',
              color: 'white',
              fontSize: '12px'
            }}>
              已选择: {selectedItem.name} {selectedItem.icon}
              <br />
              点击地图空位置放置，点击道具取消选择
            </div>
          )}

          {Object.entries(itemCategories).map(([category, items]) => (
            <div key={category} style={{ marginBottom: '15px' }}>
              <div 
                style={{ 
                  fontSize: '12px', 
                  color: '#ccc', 
                  marginBottom: '8px',
                  borderBottom: '1px solid #444',
                  paddingBottom: '4px'
                }}
              >
                {category}
              </div>
              <div 
                style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(4, 1fr)', 
                  gap: '8px' 
                }}
              >
                {items.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => handleItemClick(item)}
                    style={{
                      padding: '8px',
                      backgroundColor: selectedItem?.id === item.id ? '#4CAF50' : '#333',
                      border: '1px solid #555',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      textAlign: 'center',
                      fontSize: '11px',
                      color: 'white',
                      transition: 'all 0.2s ease',
                      ':hover': {
                        backgroundColor: '#444'
                      }
                    }}
                    onMouseEnter={(e) => {
                      if (selectedItem?.id !== item.id) {
                        e.target.style.backgroundColor = '#444';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (selectedItem?.id !== item.id) {
                        e.target.style.backgroundColor = '#333';
                      }
                    }}
                    title={item.description}
                  >
                    <div style={{ fontSize: '16px', marginBottom: '2px', display: 'flex', justifyContent: 'center' }}>
                      <Icon icon={item.icon} width="16" height="16" style={{ color: 'white' }} />
                    </div>
                    <div style={{ fontSize: '9px', lineHeight: '1.2' }}>
                      {item.name}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Clear Selection Button */}
          {selectedItem && (
            <button
              onClick={onClearSelection}
              style={{
                width: '100%',
                padding: '8px',
                backgroundColor: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px',
                marginTop: '10px'
              }}
            >
              取消选择
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ItemToolbar;