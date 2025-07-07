/**
 * Map visualization component
 */
import React from 'react';
import useWorldStore from '../store/worldStore';

function MapView() {
  const { worldState, selectedAgent, setSelectedAgent } = useWorldStore();
  
  if (!worldState) {
    return (
      <div className="map-container">
        <div style={{ 
          textAlign: 'center',
          color: '#666',
          fontSize: '18px'
        }}>
          World not initialized
        </div>
      </div>
    );
  }
  
  const { game_map, agents } = worldState;
  
  // Create grid template
  const gridStyle = {
    gridTemplateColumns: `repeat(${game_map.width}, 30px)`,
    gridTemplateRows: `repeat(${game_map.height}, 30px)`
  };
  
  // Create cells array
  const cells = [];
  for (let y = 0; y < game_map.height; y++) {
    for (let x = 0; x < game_map.width; x++) {
      const cellKey = `${x},${y}`;
      const cellType = game_map.cells[cellKey] || 'Cell_Block';
      
      // Find agents at this position
      const agentsAtPosition = Object.values(agents).filter(
        agent => agent.position[0] === x && agent.position[1] === y
      );
      
      // Find items at this position
      const itemsAtPosition = game_map.items[cellKey] || [];
      
      cells.push(
        <div
          key={cellKey}
          className={`map-cell ${cellType}`}
          onClick={() => {
            if (agentsAtPosition.length > 0) {
              setSelectedAgent(agentsAtPosition[0]);
            }
          }}
          title={`(${x}, ${y}) - ${cellType}${itemsAtPosition.length > 0 ? ` - ${itemsAtPosition.length} items` : ''}`}
        >
          {/* Render items */}
          {itemsAtPosition.length > 0 && (
            <div style={{
              position: 'absolute',
              top: '2px',
              right: '2px',
              fontSize: '8px',
              color: '#fff',
              backgroundColor: 'rgba(0,0,0,0.7)',
              borderRadius: '2px',
              padding: '1px 2px'
            }}>
              {itemsAtPosition.length}
            </div>
          )}
          
          {/* Render agents */}
          {agentsAtPosition.map(agent => (
            <div
              key={agent.agent_id}
              className={`agent-marker ${agent.role} ${
                selectedAgent?.agent_id === agent.agent_id ? 'selected' : ''
              }`}
              title={`${agent.name} (${agent.role})\nHP: ${agent.hp}, Sanity: ${agent.sanity}`}
            >
              {agent.role === 'Guard' ? 'G' : 'P'}
            </div>
          ))}
        </div>
      );
    }
  }
  
  return (
    <div className="map-container">
      <div>
        <h3 style={{ textAlign: 'center', marginBottom: '20px' }}>
          Prison Map ({game_map.width}x{game_map.height})
        </h3>
        
        <div className="map-grid" style={gridStyle}>
          {cells}
        </div>
        
        <div style={{ 
          marginTop: '20px',
          textAlign: 'center',
          fontSize: '12px',
          color: '#ccc'
        }}>
          <div>
            <span style={{ color: '#4a4a4a', backgroundColor: '#4a4a4a', padding: '2px 4px', margin: '2px' }}>■</span> Cell Block
            <span style={{ color: '#8B4513', backgroundColor: '#8B4513', padding: '2px 4px', margin: '2px' }}>■</span> Cafeteria
            <span style={{ color: '#228B22', backgroundColor: '#228B22', padding: '2px 4px', margin: '2px' }}>■</span> Yard
            <span style={{ color: '#800000', backgroundColor: '#800000', padding: '2px 4px', margin: '2px' }}>■</span> Solitary
            <span style={{ color: '#000080', backgroundColor: '#000080', padding: '2px 4px', margin: '2px' }}>■</span> Guard Room
          </div>
          <div style={{ marginTop: '10px' }}>
            <span style={{ color: '#0066cc', backgroundColor: '#0066cc', padding: '2px 4px', margin: '2px', borderRadius: '50%' }}>G</span> Guard
            <span style={{ color: '#cc6600', backgroundColor: '#cc6600', padding: '2px 4px', margin: '2px', borderRadius: '50%' }}>P</span> Prisoner
          </div>
        </div>
      </div>
    </div>
  );
}

export default MapView;