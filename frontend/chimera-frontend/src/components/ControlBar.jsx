import React from 'react';

const ControlBar = ({ simulationStatus, connectionStatus, onControlCommand }) => {
  const { isRunning, isPaused, tick, speed, experimentId, experimentStartTime } = simulationStatus;

  const handlePlayPause = () => {
    if (!isRunning) {
      onControlCommand('play');
    } else if (isPaused) {
      onControlCommand('resume');
    } else {
      onControlCommand('pause');
    }
  };

  const handleStop = () => {
    onControlCommand('stop');
  };

  const handleSpeedChange = (event) => {
    const newSpeed = parseFloat(event.target.value);
    onControlCommand('set_speed', newSpeed);
  };

  const getPlayPauseText = () => {
    if (!isRunning && !experimentId) return 'New Experiment';
    if (!isRunning) return 'Resume Experiment';
    return isPaused ? 'Resume' : 'Pause';
  };

  const getStatusText = () => {
    if (!isRunning && !experimentId) return 'Ready';
    if (!isRunning) return 'Experiment Stopped';
    return isPaused ? 'Paused' : 'Running';
  };

  // Only disable controls if connection is completely failed or disconnected
  const isControlsDisabled = connectionStatus === 'Failed' || connectionStatus === 'Disconnected';

  return (
    <div className="control-bar">
      <div className="control-group">
        <button
          className={`control-button ${!isRunning || isPaused ? 'primary' : ''}`}
          onClick={handlePlayPause}
          disabled={isControlsDisabled}
        >
          {getPlayPauseText()}
        </button>
        
        <button
          className="control-button danger"
          onClick={handleStop}
          disabled={!isRunning || isControlsDisabled}
        >
          Stop
        </button>
      </div>

      <div className="control-group speed-control">
        <label htmlFor="speed-select">Speed:</label>
        <select
          id="speed-select"
          className="speed-select"
          value={speed}
          onChange={handleSpeedChange}
          disabled={isControlsDisabled}
        >
          <option value={0.5}>0.5x</option>
          <option value={1.0}>1.0x</option>
          <option value={2.0}>2.0x</option>
          <option value={5.0}>5.0x</option>
        </select>
      </div>

      <div className="control-group">
        <span className="detail-label">Tick:</span>
        <span className="detail-value">{tick}</span>
      </div>

      <div className="control-group">
        <span className="detail-label">Status:</span>
        <span className="detail-value">{getStatusText()}</span>
      </div>

      {experimentId && (
        <div className="control-group">
          <span className="detail-label">Experiment:</span>
          <span className="detail-value experiment-id">{experimentId}</span>
        </div>
      )}

      {experimentStartTime && (
        <div className="control-group">
          <span className="detail-label">Started:</span>
          <span className="detail-value">
            {new Date(experimentStartTime).toLocaleTimeString()}
          </span>
        </div>
      )}

      <div className="control-group">
        <button
          className="control-button secondary"
          onClick={() => onControlCommand('new_experiment')}
          disabled={isControlsDisabled}
          title="Start a new experiment with fresh configuration"
        >
          New Experiment
        </button>
        
        <button
          className="control-button secondary"
          onClick={() => onControlCommand('show_history')}
          disabled={isControlsDisabled}
          title="View experiment history"
        >
          History
        </button>
      </div>

      <div className="status-indicator">
        <span className="detail-label">Connection:</span>
        <div className={`status-dot ${
          connectionStatus === 'Connected' ? 'connected' : 
          connectionStatus === 'Connecting' || connectionStatus === 'Reconnecting' ? 'connecting' : 
          'disconnected'
        }`}></div>
        <span className="detail-value">{connectionStatus}</span>
      </div>
    </div>
  );
};

export default ControlBar;