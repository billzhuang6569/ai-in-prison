import React, { useState, useEffect } from 'react';

const ExperimentHistory = ({ isVisible, onClose, onLoadExperiment, onReplayExperiment }) => {
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

  const handleExportExperiment = async (experimentId, format) => {
    try {
      const response = await fetch(`http://localhost:8000/api/export/${experimentId}?format=${format}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${experimentId}_export.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        console.error('Export failed:', response.statusText);
        alert('Export failed. Please try again.');
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed. Please check your connection.');
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
                      onClick={() => onReplayExperiment && onReplayExperiment(experiment.full_id || experiment.id)}
                      disabled={experiment.status === 'running'}
                    >
                      Replay
                    </button>
                    
                    <div className="export-dropdown">
                      <button className="config-button export-btn">
                        Export ▼
                      </button>
                      <div className="export-options">
                        <button 
                          onClick={() => handleExportExperiment(experiment.full_id || experiment.id, 'json')}
                          className="export-option"
                        >
                          JSON
                        </button>
                        <button 
                          onClick={() => handleExportExperiment(experiment.full_id || experiment.id, 'csv')}
                          className="export-option"
                        >
                          CSV
                        </button>
                      </div>
                    </div>
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