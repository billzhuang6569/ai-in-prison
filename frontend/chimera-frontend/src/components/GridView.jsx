import React from 'react';

const GridView = ({ worldState, selectedAgent, onAgentSelect, agentTrajectories }) => {
  const getItemEmoji = (itemType) => {
    const emojiMap = {
      'Food': '🍞',
      'Readable': '📜',
      'Key': '🗝️',
      'Weapon': '🗡️',
      'Consumable': '💊'
    };
    return emojiMap[itemType] || '📦';
  };

  const getAgentColor = (agentId) => {
    const colorMap = {
      'guard_01': '#007acc',
      'guard_02': '#0099ff',
      'prisoner_01': '#d73a49',
      'prisoner_02': '#ff4757'
    };
    return colorMap[agentId] || '#666';
  };

  const renderTrajectoryLines = (agentId, trajectory) => {
    if (!trajectory || trajectory.length < 2) return null;

    const lines = [];
    const cellSize = 40;
    const cellGap = 1;
    const totalCellSize = cellSize + cellGap;
    const color = getAgentColor(agentId);

    for (let i = 0; i < trajectory.length - 1; i++) {
      const from = trajectory[i];
      const to = trajectory[i + 1];
      
      // Calculate opacity based on age (newer = more opaque)
      const age = trajectory.length - i - 1;
      let opacity;
      if (age <= 3) opacity = 1.0;      // Last 3 steps: solid
      else if (age <= 6) opacity = 0.5; // 4-6 steps: 50% transparent
      else opacity = 0.3;               // 7+ steps: 70% transparent

      const x1 = from.x * totalCellSize + cellSize / 2;
      const y1 = from.y * totalCellSize + cellSize / 2;
      const x2 = to.x * totalCellSize + cellSize / 2;
      const y2 = to.y * totalCellSize + cellSize / 2;

      lines.push(
        <line
          key={`${agentId}-${i}`}
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke={color}
          strokeWidth="3"
          strokeOpacity={opacity}
          strokeLinecap="round"
        />
      );
    }

    return lines;
  };
  if (!worldState) {
    return (
      <div className="grid-container">
        <div className="loading">Loading simulation...</div>
      </div>
    );
  }

  const { map, agents } = worldState;
  const { size, grid } = map;
  const [width, height] = size;

  // Create a map of cell types for quick lookup
  const cellTypeMap = {};
  grid.forEach(cell => {
    const key = `${cell.x},${cell.y}`;
    cellTypeMap[key] = cell.type;
  });

  // Create a map of agent positions for quick lookup
  const agentPositionMap = {};
  agents.forEach(agent => {
    const key = `${agent.position.x},${agent.position.y}`;
    agentPositionMap[key] = agent;
  });

  const handleCellClick = (x, y, event) => {
    // Don't handle cell click if an agent was clicked directly
    if (event && event.target.closest('.agent')) {
      return;
    }
    
    const agentsAtPosition = agents.filter(agent => 
      agent.position.x === x && agent.position.y === y
    );
    if (agentsAtPosition.length > 0) {
      // If multiple agents, select the first one or cycle through them
      const currentIndex = agentsAtPosition.findIndex(agent => agent.id === selectedAgent);
      const nextIndex = currentIndex >= 0 ? (currentIndex + 1) % agentsAtPosition.length : 0;
      onAgentSelect(agentsAtPosition[nextIndex].id);
    }
  };

  const handleAgentClick = (agentId, event) => {
    event.preventDefault();
    event.stopPropagation();
    console.log(`Agent clicked: ${agentId}`);
    console.log('Event target:', event.target);
    console.log('Event currentTarget:', event.currentTarget);
    onAgentSelect(agentId);
  };

  const renderCell = (x, y) => {
    const key = `${x},${y}`;
    const cellType = cellTypeMap[key] || 'Floor';
    const agentsAtPosition = agents.filter(agent => 
      agent.position.x === x && agent.position.y === y
    );
    
    // Check for items at this position
    const items = worldState.objects?.filter(obj => {
      const pos = obj.position;
      return pos && pos.x === x && pos.y === y;
    }) || [];
    
    let cellClass = 'grid-cell';
    if (cellType === 'Wall') {
      cellClass += ' wall';
    } else {
      cellClass += ' floor';
    }

    return (
      <div
        key={key}
        className={cellClass}
        onClick={(e) => handleCellClick(x, y, e)}
        title={items.length > 0 ? `Items: ${items.map(i => i.name).join(', ')}` : ''}
        style={{ 
          position: 'relative',
          zIndex: 1
        }}
      >
        {/* Render items */}
        {items.length > 0 && agentsAtPosition.length === 0 && (
          <div className="item-indicator" title={items.map(i => i.name).join(', ')}>
            {getItemEmoji(items[0].type)}
          </div>
        )}
        
        {/* Render agents - simplified approach */}
        {agentsAtPosition.map((agent, index) => (
          <div
            key={agent.id}
            className={`agent ${agent.role} ${selectedAgent === agent.id ? 'selected' : ''}`}
            style={{
              position: 'absolute',
              top: agentsAtPosition.length > 1 ? `${index * 8}px` : '50%',
              left: agentsAtPosition.length > 1 ? `${index * 8}px` : '50%',
              transform: agentsAtPosition.length === 1 ? 'translate(-50%, -50%)' : 'none',
              zIndex: 100 + index,
              cursor: 'pointer',
              pointerEvents: 'auto'
            }}
            title={`${agent.id} (${agent.role})${items.length > 0 ? ` - Items here: ${items.map(i => i.name).join(', ')}` : ''}`}
            onClick={(e) => handleAgentClick(agent.id, e)}
          >
            <div className="agent-id">
              {agent.id.split('_')[1] || agent.id.charAt(0).toUpperCase()}
            </div>
            {agent.inventory && agent.inventory.length > 0 && (
              <div className="agent-inventory-indicator">
                {agent.inventory.length}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const gridStyle = {
    gridTemplateColumns: `repeat(${width}, 1fr)`,
    gridTemplateRows: `repeat(${height}, 1fr)`
  };

  return (
    <div className="grid-container">
      <div className="grid-info">
        <h2>Project Chimera - Prison Simulation</h2>
        <p>Grid Size: {width} × {height} | Agents: {agents.length} | Tick: {worldState.tick}</p>
        <p>Click on an agent to view their details and inner thoughts</p>
      </div>
      
      <div className="grid-wrapper">
        {/* Coordinate labels */}
        <div className="coordinate-labels">
          {/* Top coordinates */}
          <div className="top-coordinates">
            {Array.from({ length: width }, (_, x) => (
              <div key={`top-${x}`} className="coordinate-label top">
                {x}
              </div>
            ))}
          </div>
          
          {/* Left coordinates */}
          <div className="left-coordinates">
            {Array.from({ length: height }, (_, y) => (
              <div key={`left-${y}`} className="coordinate-label left">
                {y}
              </div>
            ))}
          </div>
        </div>
        
        {/* SVG overlay for trajectory lines */}
        <svg className="trajectory-overlay" style={{
          position: 'absolute',
          top: 30,
          left: 30,
          width: width * 41,
          height: height * 41,
          pointerEvents: 'none',
          zIndex: 1
        }}>
          {agentTrajectories && Object.entries(agentTrajectories).map(([agentId, trajectory]) => {
            console.log(`Rendering trajectory for ${agentId}:`, trajectory);
            return renderTrajectoryLines(agentId, trajectory);
          })}
          
          {/* Debug: Add a test line to verify SVG is working */}
          <line
            x1="20"
            y1="20"
            x2="80"
            y2="80"
            stroke="yellow"
            strokeWidth="2"
            strokeOpacity="0.8"
          />
        </svg>
        
        {/* Grid cells */}
        <div className="world-grid" style={{
          ...gridStyle,
          marginTop: '30px',
          marginLeft: '30px',
          zIndex: 2
        }}>
          {Array.from({ length: height }, (_, y) =>
            Array.from({ length: width }, (_, x) => renderCell(x, y))
          )}
        </div>
      </div>

      <div className="grid-legend">
        <div className="legend-item">
          <div className="agent guard"></div>
          <span>Guards</span>
        </div>
        <div className="legend-item">
          <div className="agent prisoner"></div>
          <span>Prisoners</span>
        </div>
        <div className="legend-item">
          <div className="grid-cell wall" style={{width: '20px', height: '20px'}}></div>
          <span>Walls</span>
        </div>
        <div className="legend-item">
          <div style={{width: '20px', height: '2px', backgroundColor: '#007acc'}}></div>
          <span>Movement Trails</span>
        </div>
      </div>
    </div>
  );
};

export default GridView;