/**
 * Speech Bubble - 对话气泡组件
 * 显示智能体的对话内容
 */
import React, { useState, useEffect } from 'react';

function SpeechBubble({ agent, message, position, onClose }) {
  const [isVisible, setIsVisible] = useState(true);
  
  useEffect(() => {
    // 5秒后自动隐藏气泡
    const timer = setTimeout(() => {
      setIsVisible(false);
      onClose();
    }, 5000);
    
    return () => clearTimeout(timer);
  }, [onClose]);
  
  if (!isVisible || !message) {
    return null;
  }
  
  // 解析消息内容，提取目标和内容
  const parseMessage = (msg) => {
    // 匹配格式: "To P2: What's up?" 或 "对 P2 说：你好吗？"
    const match = msg.match(/(?:To|对)\s+([^:：]+)[:：]\s*(.+)/);
    if (match) {
      return {
        target: match[1].trim(),
        content: match[2].trim()
      };
    }
    return {
      target: null,
      content: msg
    };
  };
  
  const parsed = parseMessage(message);
  
  return (
    <div 
      className="speech-bubble"
      style={{
        position: 'absolute',
        left: `${(position.x + 1) * 46}px`, // 使用新的45px单元格大小 + 1px gap
        top: `${position.y * 46 - 15}px`, // 稍微向上偏移
        zIndex: 20
      }}
    >
      <div className="bubble-content">
        {parsed.target && (
          <div className="speech-target">
            → {parsed.target}
          </div>
        )}
        <div className="speech-text">
          {parsed.content}
        </div>
      </div>
      
      <button 
        className="bubble-close"
        onClick={() => {
          setIsVisible(false);
          onClose();
        }}
        title="关闭"
      >
        ×
      </button>
      
      <style jsx>{`
        .speech-bubble {
          background: rgba(255, 255, 255, 0.95);
          border: 2px solid #3498db;
          border-radius: 12px;
          padding: 8px 12px;
          max-width: 180px;
          min-width: 100px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
          font-family: 'Arial', sans-serif;
          font-size: 11px;
          line-height: 1.3;
          position: relative;
          animation: bubbleAppear 0.3s ease-out;
          backdrop-filter: blur(5px);
        }
        
        .speech-bubble::before {
          content: '';
          position: absolute;
          left: -8px;
          top: 15px;
          width: 0;
          height: 0;
          border-style: solid;
          border-width: 6px 8px 6px 0;
          border-color: transparent #3498db transparent transparent;
        }
        
        .speech-bubble::after {
          content: '';
          position: absolute;
          left: -6px;
          top: 16px;
          width: 0;
          height: 0;
          border-style: solid;
          border-width: 5px 7px 5px 0;
          border-color: transparent rgba(255, 255, 255, 0.95) transparent transparent;
        }
        
        .bubble-content {
          color: #2c3e50;
        }
        
        .speech-target {
          font-size: 9px;
          color: #e74c3c;
          font-weight: bold;
          margin-bottom: 3px;
          padding: 2px 4px;
          background: rgba(231, 76, 60, 0.1);
          border-radius: 3px;
          border-left: 2px solid #e74c3c;
        }
        
        .speech-text {
          color: #2c3e50;
          font-weight: 500;
          word-wrap: break-word;
        }
        
        .bubble-close {
          position: absolute;
          top: -5px;
          right: -5px;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #e74c3c;
          color: white;
          border: none;
          font-size: 10px;
          font-weight: bold;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
          transition: all 0.2s ease;
        }
        
        .bubble-close:hover {
          background: #c0392b;
          transform: scale(1.1);
        }
        
        @keyframes bubbleAppear {
          0% {
            opacity: 0;
            transform: scale(0.8) translateY(10px);
          }
          100% {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
        
        .speech-bubble:hover {
          box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
          transform: translateY(-1px);
          transition: all 0.2s ease;
        }
      `}</style>
    </div>
  );
}

export default SpeechBubble;