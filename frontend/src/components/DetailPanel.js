/**
 * Detail panel for selected agent information
 */
import React from 'react';
import useWorldStore from '../store/worldStore';

function DetailPanel() {
  const { selectedAgent, worldState } = useWorldStore();
  
  if (!selectedAgent) {
    return (
      <div className="panel">
        <h2>Agent Details</h2>
        <p style={{ color: '#666' }}>
          Click on an agent in the map to view their details
        </p>
      </div>
    );
  }
  
  const renderStatBar = (label, value, max, className) => (
    <div className="stat-bar">
      <div className="stat-label">{label}:</div>
      <div className="stat-value">
        <div 
          className={`stat-fill ${className}`}
          style={{ width: `${(value / max) * 100}%` }}
        />
      </div>
      <div className="stat-number">{value}</div>
    </div>
  );
  
  return (
    <div className="panel">
      <h2>Agent Details</h2>
      
      <div className="agent-details">
        <div className="agent-name">{selectedAgent.name}</div>
        <div className="agent-role">{selectedAgent.role}</div>
        
        <div style={{ marginBottom: '15px' }}>
          <strong>Position:</strong> ({selectedAgent.position[0]}, {selectedAgent.position[1]})
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <strong>Action Points:</strong> {selectedAgent.action_points}/3
        </div>
        
        <h3>Status</h3>
        {renderStatBar('HP', selectedAgent.hp, 100, 'hp')}
        {renderStatBar('Sanity', selectedAgent.sanity, 100, 'sanity')}
        {renderStatBar('Hunger', selectedAgent.hunger, 100, 'hunger')}
        {renderStatBar('Thirst', selectedAgent.thirst, 100, 'thirst')}
        {renderStatBar('Strength', selectedAgent.strength, 100, 'strength')}
        
        {selectedAgent.status_tags.length > 0 && (
          <div>
            <h3>Status Tags</h3>
            <div className="status-tags">
              {selectedAgent.status_tags.map(tag => (
                <span key={tag} className="status-tag">{tag}</span>
              ))}
            </div>
          </div>
        )}
        
        <h3>Personality Traits</h3>
        {renderStatBar('Aggression', selectedAgent.traits.aggression, 100, 'hp')}
        {renderStatBar('Empathy', selectedAgent.traits.empathy, 100, 'sanity')}
        {renderStatBar('Logic', selectedAgent.traits.logic, 100, 'hunger')}
        {renderStatBar('Obedience', selectedAgent.traits.obedience, 100, 'thirst')}
        {renderStatBar('Resilience', selectedAgent.traits.resilience, 100, 'strength')}
        
        <h3>Inventory</h3>
        {selectedAgent.inventory.length > 0 ? (
          <div>
            {selectedAgent.inventory.map(item => (
              <div key={item.item_id} style={{
                padding: '5px',
                backgroundColor: '#444',
                marginBottom: '5px',
                borderRadius: '3px',
                fontSize: '12px'
              }}>
                <strong>{item.name}</strong><br />
                {item.description}
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#666', fontSize: '12px' }}>No items</p>
        )}
        
        <h3>Relationships</h3>
        {Object.keys(selectedAgent.relationships).length > 0 ? (
          <div>
            {Object.entries(selectedAgent.relationships).map(([targetId, relationship]) => {
              const targetAgent = worldState?.agents[targetId];
              return (
                <div key={targetId} style={{
                  padding: '8px',
                  backgroundColor: '#444',
                  marginBottom: '8px',
                  borderRadius: '3px',
                  fontSize: '12px'
                }}>
                  <div style={{ fontWeight: 'bold' }}>
                    {targetAgent?.name || targetId}
                  </div>
                  <div className="stat-bar">
                    <div className="stat-label">Relation:</div>
                    <div className="stat-value">
                      <div 
                        className="stat-fill sanity"
                        style={{ width: `${relationship.score}%` }}
                      />
                    </div>
                    <div className="stat-number">{relationship.score}</div>
                  </div>
                  <div style={{ color: '#ccc', fontSize: '10px', marginTop: '5px' }}>
                    {relationship.context}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p style={{ color: '#666', fontSize: '12px' }}>No relationships</p>
        )}
        
        <h3>Recent Memory</h3>
        {selectedAgent.memory.episodic.length > 0 ? (
          <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
            {selectedAgent.memory.episodic.slice(-10).reverse().map((memory, index) => (
              <div key={index} style={{
                padding: '5px',
                backgroundColor: '#444',
                marginBottom: '5px',
                borderRadius: '3px',
                fontSize: '11px',
                color: '#ccc'
              }}>
                {memory}
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#666', fontSize: '12px' }}>No recent memories</p>
        )}
        
        <h3>Objectives</h3>
        {selectedAgent.objectives.length > 0 ? (
          <div>
            {selectedAgent.objectives.map(objective => (
              <div key={objective.objective_id} style={{
                padding: '8px',
                backgroundColor: '#444',
                marginBottom: '8px',
                borderRadius: '3px',
                fontSize: '12px'
              }}>
                <div style={{ fontWeight: 'bold' }}>
                  {objective.name} ({objective.type})
                </div>
                <div style={{ color: '#ccc', fontSize: '10px' }}>
                  {objective.description}
                </div>
                <div style={{ 
                  color: objective.is_completed ? '#4CAF50' : '#FFC107',
                  fontSize: '10px',
                  marginTop: '5px'
                }}>
                  {objective.is_completed ? 'Completed' : 'In Progress'}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#666', fontSize: '12px' }}>No objectives</p>
        )}
      </div>
    </div>
  );
}

export default DetailPanel;