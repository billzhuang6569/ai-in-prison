import React, { useState, useEffect } from 'react';

const ExperimentHistory = ({ isVisible, onClose, onLoadExperiment }) => {
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isVisible) {
      fetchExperiments();
    }
  }, [isVisible]);

  const fetchExperiments = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/experiments');
      if (response.ok) {
        const data = await response.json();
        setExperiments(data.experiments || []);
      }
    } catch (error) {
      console.error('Failed to fetch experiments:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (startTime, endTime) => {
    if (!endTime) return 'Running';
    const start = new Date(startTime);
    const end = new Date(endTime);
    const duration = Math.floor((end - start) / 1000);
    return `${duration}s`;
  };

  const formatDateTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  if (!isVisible) return null;

  return (
    <div className="experiment-config-overlay">
      <div className="experiment-config-modal">
        <div className="config-header">
          <h2>Experiment History</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <div className="config-content">
          {loading ? (
            <div className="loading">Loading experiments...</div>
          ) : experiments.length === 0 ? (
            <div className="no-experiments">
              <p>No experiments found.</p>
              <p>Start your first experiment to see it here.</p>
            </div>
          ) : (
            <div className="experiments-list">
              {experiments.map((experiment) => (
                <div key={experiment.id} className="experiment-item">
                  <div className="experiment-header">
                    <span className="experiment-id">{experiment.id}</span>
                    <span className="experiment-status">
                      {experiment.status === 'running' ? '🟢 Running' : 
                       experiment.status === 'completed' ? '✅ Completed' : 
                       '⏸️ Stopped'}
                    </span>
                  </div>
                  
                  <div className="experiment-details">
                    <div className="detail-row">
                      <span className="detail-label">Started:</span>
                      <span className="detail-value">{formatDateTime(experiment.start_time)}</span>
                    </div>
                    
                    <div className="detail-row">
                      <span className="detail-label">Duration:</span>
                      <span className="detail-value">{formatDuration(experiment.start_time, experiment.end_time)}</span>
                    </div>
                    
                    <div className="detail-row">
                      <span className="detail-label">Final Tick:</span>
                      <span className="detail-value">{experiment.final_tick || experiment.current_tick || 0}</span>
                    </div>
                    
                    <div className="detail-row">
                      <span className="detail-label">Agents:</span>
                      <span className="detail-value">{experiment.agent_count}</span>
                    </div>
                  </div>
                  
                  <div className="experiment-actions">
                    <button
                      className="config-button secondary"
                      onClick={() => onLoadExperiment(experiment.id)}
                      disabled={experiment.status === 'running'}
                    >
                      Load
                    </button>
                    
                    <button
                      className="config-button"
                      onClick={() => window.open(`/api/experiments/${experiment.id}/download`, '_blank')}
                    >
                      Download
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="config-footer">
          <button className="config-button secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExperimentHistory;