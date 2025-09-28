import React from 'react';

const SpeechBubble = ({ content, agentId, position, role, bubbleId, layoutOffset }) => {
  const getBubbleStyle = () => {
    const cellSize = 40;
    const cellGap = 1;
    const totalCellSize = cellSize + cellGap;
    
    // Calculate base position
    const baseX = position.x * totalCellSize + cellSize / 2;
    const baseY = position.y * totalCellSize + cellSize / 2;
    
    // Apply smart layout offset if provided
    const offsetY = layoutOffset?.y || -60; // Above the agent by default
    const offsetX = layoutOffset?.x || 0;
    
    return {
      position: 'absolute',
      left: `${baseX + offsetX}px`,
      top: `${baseY + offsetY}px`,
      transform: 'translateX(-50%)',
      zIndex: 200 + (bubbleId || 0), // High z-index to appear above everything
      pointerEvents: 'none'
    };
  };

  const getRoleColor = () => {
    switch (role) {
      case 'guard':
        return '#007acc';
      case 'prisoner':
        return '#d73a49';
      default:
        return '#666';
    }
  };

  if (!content || content.trim() === '') {
    return null;
  }

  return (
    <div className="speech-bubble" style={getBubbleStyle()}>
      <div 
        className="bubble-content"
        style={{
          backgroundColor: 'rgba(0, 0, 0, 0.9)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: '12px',
          fontSize: '12px',
          maxWidth: '200px',
          wordWrap: 'break-word',
          border: `2px solid ${getRoleColor()}`,
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
          position: 'relative'
        }}
      >
        <div className="agent-name" style={{
          fontSize: '10px',
          fontWeight: 'bold',
          color: getRoleColor(),
          marginBottom: '4px'
        }}>
          {agentId}
        </div>
        <div className="speech-text">
          {content}
        </div>
        
        {/* Speech bubble tail */}
        <div 
          className="bubble-tail"
          style={{
            position: 'absolute',
            bottom: '-8px',
            left: '50%',
            transform: 'translateX(-50%)',
            width: '0',
            height: '0',
            borderLeft: '8px solid transparent',
            borderRight: '8px solid transparent',
            borderTop: `8px solid ${getRoleColor()}`
          }}
        />
      </div>
    </div>
  );
};

export default SpeechBubble;