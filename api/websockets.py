"""
WebSocket handling for real-time communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio
from core.engine import GameEngine
from models.schemas import WorldState

router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.game_engine = GameEngine()
        self.game_engine.set_broadcast_callback(self.broadcast_world_state)
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Send initial world state if available
        if self.game_engine.get_world_state():
            await self.send_to_client(websocket, {
                "type": "world_update",
                "payload": self.game_engine.get_world_state().dict()
            })
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_to_client(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending message to client: {e}")
    
    async def broadcast_world_state(self, world_state: WorldState):
        """Broadcast world state to all connected clients"""
        if not self.active_connections:
            return
        
        message = {
            "type": "world_update",
            "payload": world_state.dict()
        }
        
        # Send to all connected clients
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def handle_client_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle incoming message from client"""
        message_type = message.get("type")
        payload = message.get("payload", {})
        
        if message_type == "start_experiment":
            await self.start_experiment()
        elif message_type == "stop_experiment":
            await self.stop_experiment()
        elif message_type == "get_world_state":
            world_state = self.game_engine.get_world_state()
            if world_state:
                await self.send_to_client(websocket, {
                    "type": "world_update",
                    "payload": world_state.dict()
                })
        else:
            await self.send_to_client(websocket, {
                "type": "error",
                "payload": {"message": f"Unknown message type: {message_type}"}
            })
    
    async def start_experiment(self, guard_count=None, prisoner_count=None):
        """Start the simulation with optional agent counts"""
        if not self.game_engine.is_running:
            # Start the game loop in background
            asyncio.create_task(self.game_engine.start_simulation(guard_count, prisoner_count))
            
            # Broadcast start notification
            await self.broadcast_message({
                "type": "experiment_started",
                "payload": {"message": "Experiment has started"}
            })
    
    async def stop_experiment(self):
        """Stop the simulation"""
        if self.game_engine.is_running:
            self.game_engine.stop_simulation()
            
            # Broadcast stop notification
            await self.broadcast_message({
                "type": "experiment_stopped",
                "payload": {"message": "Experiment has stopped"}
            })
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast generic message to all clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await manager.handle_client_message(websocket, message)
            except json.JSONDecodeError:
                await manager.send_to_client(websocket, {
                    "type": "error",
                    "payload": {"message": "Invalid JSON format"}
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)