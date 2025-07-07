/**
 * Zustand store for world state management
 */
import { create } from 'zustand';

const useWorldStore = create((set, get) => ({
  // World state
  worldState: null,
  isConnected: false,
  selectedAgent: null,
  
  // WebSocket connection
  socket: null,
  
  // Actions
  setWorldState: (worldState) => set({ worldState }),
  setConnected: (isConnected) => set({ isConnected }),
  setSelectedAgent: (agent) => set({ selectedAgent: agent }),
  
  // Connect to WebSocket
  connect: () => {
    const socket = new WebSocket('ws://localhost:24861/ws');
    
    socket.onopen = () => {
      console.log('Connected to WebSocket');
      set({ isConnected: true, socket });
      
      // Request initial world state
      socket.send(JSON.stringify({
        type: 'get_world_state',
        payload: {}
      }));
    };
    
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case 'world_update':
            set({ worldState: message.payload });
            break;
          case 'experiment_started':
            console.log('Experiment started');
            break;
          case 'experiment_stopped':
            console.log('Experiment stopped');
            break;
          case 'error':
            console.error('Server error:', message.payload.message);
            break;
          default:
            console.log('Unknown message type:', message.type);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    socket.onclose = () => {
      console.log('WebSocket connection closed');
      set({ isConnected: false, socket: null });
    };
    
    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  },
  
  // Disconnect WebSocket
  disconnect: () => {
    const { socket } = get();
    if (socket) {
      socket.close();
    }
  },
  
  // Send message to server
  sendMessage: (type, payload = {}) => {
    const { socket } = get();
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type, payload }));
    }
  },
  
  // Start experiment
  startExperiment: () => {
    const { sendMessage } = get();
    sendMessage('start_experiment');
  },
  
  // Stop experiment
  stopExperiment: () => {
    const { sendMessage } = get();
    sendMessage('stop_experiment');
  }
}));

export default useWorldStore;