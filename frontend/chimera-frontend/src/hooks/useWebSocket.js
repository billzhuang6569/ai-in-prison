import { useState, useEffect, useRef, useCallback } from 'react';

const useWebSocket = (url, options = {}) => {
  const [connectionStatus, setConnectionStatus] = useState('Connecting');
  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectInterval = 3000; // 3 seconds
  const isManuallyDisconnected = useRef(false);

  const { onMessage, onOpen, onClose, onError } = options;

  const connect = useCallback(() => {
    try {
      // Prevent multiple connection attempts
      if (ws.current && (ws.current.readyState === WebSocket.CONNECTING || ws.current.readyState === WebSocket.OPEN)) {
        return;
      }
      
      // Clear any existing connection
      if (ws.current) {
        ws.current.close();
      }
      
      ws.current = new WebSocket(url);
      
      ws.current.onopen = (event) => {
        console.log('WebSocket connected');
        setConnectionStatus('Connected');
        reconnectAttempts.current = 0;
        isManuallyDisconnected.current = false;
        if (onOpen) onOpen(event);
      };

      ws.current.onmessage = (event) => {
        setLastMessage(event);
        if (onMessage) onMessage(event);
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        
        // Only attempt to reconnect if not manually disconnected and within retry limit
        if (!isManuallyDisconnected.current && event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          console.log(`Attempting to reconnect... (${reconnectAttempts.current}/${maxReconnectAttempts})`);
          setConnectionStatus('Reconnecting');
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval * Math.min(reconnectAttempts.current, 3)); // Cap exponential backoff
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setConnectionStatus('Failed');
          console.error('Max reconnection attempts reached');
        } else {
          setConnectionStatus('Disconnected');
        }
        
        if (onClose) onClose(event);
      };

      ws.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        // Don't immediately set to error state, let onclose handle it
        if (onError) onError(event);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('Error');
    }
  }, [url, onMessage, onOpen, onClose, onError]);

  const disconnect = useCallback(() => {
    isManuallyDisconnected.current = true;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (ws.current) {
      ws.current.close(1000, 'Manual disconnect');
      ws.current = null;
    }
    
    setConnectionStatus('Disconnected');
  }, []);

  const sendMessage = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      try {
        const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
        ws.current.send(messageStr);
        return true;
      } catch (error) {
        console.error('Failed to send message:', error);
        return false;
      }
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
      return false;
    }
  }, []);

  const getReadyState = useCallback(() => {
    if (!ws.current) return WebSocket.CLOSED;
    return ws.current.readyState;
  }, []);

  // Connect on mount
  useEffect(() => {
    connect();
    
    // Cleanup on unmount
    return () => {
      isManuallyDisconnected.current = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (ws.current) {
        ws.current.close(1000, 'Component unmounting');
      }
    };
  }, [connect]);

  return {
    connectionStatus,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: connect,
    getReadyState
  };
};

export default useWebSocket;