"""
Main API Server for Project Chimera

This module implements the FastAPI server that runs the main simulation loop
and provides WebSocket communication with the frontend.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Set, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from src.core.engine import SimulationEngine
from src.agents.agent import AIAgent
from src.logging.logger import SimulationLogger
from src.core.inventory_system import ItemManager
from config import Config


class WebSocketManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.focused_agents: Dict[WebSocket, str] = {}  # Track which agent each client is focusing on
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.remove(websocket)
        if websocket in self.focused_agents:
            del self.focused_agents[websocket]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending message to websocket: {e}")
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected WebSockets."""
        if self.active_connections:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    print(f"Error broadcasting to websocket: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.disconnect(connection)
    
    async def send_agent_log_update(self, agent_id: str, log_data: dict):
        """Send agent log update to clients focusing on this agent."""
        message = {
            "type": "agent_log_update",
            "agent_id": agent_id,
            "data": log_data
        }
        
        for websocket, focused_agent in self.focused_agents.items():
            if focused_agent == agent_id:
                await self.send_personal_message(message, websocket)


class SimulationController:
    """Controls the main simulation loop."""
    
    def __init__(self):
        self.engine = SimulationEngine()
        self.logger = None  # Will be initialized per experiment
        self.agents: List[AIAgent] = []
        self.current_state: Dict[str, Any] = {}
        self.websocket_manager = WebSocketManager()
        
        # Simulation control
        self.is_running = False
        self.is_paused = True
        self.tick_speed = 1.0  # seconds per tick
        self.simulation_task = None
        
        # Experiment management
        self.current_experiment_id = None
        self.experiment_start_time = None
        
        # Initialize default world state
        self._initialize_world()
    
    def _initialize_world(self):
        """Initialize the default world state and agents."""
        # Create a simple prison layout (10x10 grid)
        self.current_state = {
            "tick": 0,
            "map": {
                "size": [10, 10],
                "grid": [
                    # Add walls around the perimeter
                    {"x": x, "y": 0, "type": "Wall"} for x in range(10)
                ] + [
                    {"x": x, "y": 9, "type": "Wall"} for x in range(10)
                ] + [
                    {"x": 0, "y": y, "type": "Wall"} for y in range(1, 9)
                ] + [
                    {"x": 9, "y": y, "type": "Wall"} for y in range(1, 9)
                ] + [
                    # Add some internal walls
                    {"x": 5, "y": y, "type": "Wall"} for y in range(3, 7)
                ]
            },
            "agents": [],
            "objects": []
        }
        
        # Create sample agents
        self._create_sample_agents()
    
    def _create_sample_agents(self):
        """Create sample agents for the simulation."""
        # Create guards
        guard1 = AIAgent(
            agent_id="guard_01",
            personality="Strict and authoritative, believes in maintaining order through discipline.",
            model_name=Config.DEFAULT_MODEL,
            role="guard"
        )
        
        guard2 = AIAgent(
            agent_id="guard_02", 
            personality="More lenient and empathetic, tries to understand prisoners' perspectives.",
            model_name=Config.DEFAULT_MODEL,
            role="guard"
        )
        
        # Create prisoners
        prisoner1 = AIAgent(
            agent_id="prisoner_01",
            personality="Rebellious and defiant, challenges authority at every opportunity.",
            model_name=Config.DEFAULT_MODEL,
            role="prisoner"
        )
        
        prisoner2 = AIAgent(
            agent_id="prisoner_02",
            personality="Quiet and observant, tries to avoid conflict and follow rules.",
            model_name=Config.DEFAULT_MODEL,
            role="prisoner"
        )
        
        self.agents = [guard1, guard2, prisoner1, prisoner2]
        
        # Add agents to world state with inventory
        self.current_state["agents"] = [
            {
                "id": "guard_01",
                "role": "guard",
                "position": {"x": 2, "y": 2},
                "status": {"energy": 100, "mood": "alert"},
                "inventory": []
            },
            {
                "id": "guard_02",
                "role": "guard", 
                "position": {"x": 7, "y": 2},
                "status": {"energy": 100, "mood": "calm"},
                "inventory": []
            },
            {
                "id": "prisoner_01",
                "role": "prisoner",
                "position": {"x": 2, "y": 7},
                "status": {"energy": 80, "mood": "restless"},
                "inventory": []
            },
            {
                "id": "prisoner_02",
                "role": "prisoner",
                "position": {"x": 7, "y": 7},
                "status": {"energy": 90, "mood": "anxious"},
                "inventory": []
            }
        ]
        
        # Add some sample items to the world
        self._add_sample_items()
    
    def _add_sample_items(self):
        """Add sample items to the world for testing."""
        item_manager = ItemManager()
        
        # Add some food rations
        food1 = item_manager.create_item("Food", {"x": 4, "y": 4})
        food2 = item_manager.create_item("Food", {"x": 6, "y": 6})
        
        # Add a note
        note = item_manager.create_item("Readable", {"x": 3, "y": 8}, 
                                       {"content": "Meet me at the cafeteria at midnight"})
        
        # Add a medkit
        medkit = item_manager.create_item("Consumable", {"x": 8, "y": 3})
        
        # Add items to world state
        self.current_state["objects"].extend([food1, food2, note, medkit])
    
    async def start_experiment_with_config(self, experiment_config: Dict[str, Any]):
        """Start a new experiment with custom configuration."""
        if self.is_running:
            await self.stop_simulation()
        
        # Create new experiment
        self.current_experiment_id = str(uuid.uuid4())[:8]
        self.experiment_start_time = datetime.now()
        
        # Initialize logger for this experiment
        experiment_session_id = f"experiment_{self.current_experiment_id}_{self.experiment_start_time.strftime('%Y%m%d_%H%M%S')}"
        self.logger = SimulationLogger(session_id=experiment_session_id)
        
        # Initialize world with custom configuration
        self._initialize_world_with_config(experiment_config)
        
        self.is_running = True
        self.is_paused = False
        self.simulation_task = asyncio.create_task(self._simulation_loop())
        
        # Broadcast experiment start
        await self.websocket_manager.broadcast({
            "type": "experiment_started",
            "experiment_id": self.current_experiment_id,
            "start_time": self.experiment_start_time.isoformat(),
            "world_state": self.current_state,
            "config": experiment_config
        })
        
        self.logger.log_event("experiment_start", {
            "experiment_id": self.current_experiment_id,
            "start_time": self.experiment_start_time.isoformat(),
            "config": experiment_config,
            "tick": self.current_state["tick"]
        })

    def _initialize_world_with_config(self, config: Dict[str, Any]):
        """Initialize world state with custom configuration."""
        map_size = config.get('mapSize', [10, 10])
        agents_config = config.get('agents', [])
        
        # Create world state
        self.current_state = {
            "tick": 0,
            "map": {
                "size": map_size,
                "grid": self._generate_map_grid(map_size)
            },
            "agents": [],
            "objects": []
        }
        
        # Create agents from configuration
        self.agents = []
        for agent_config in agents_config:
            agent = AIAgent(
                agent_id=agent_config['id'],
                personality=agent_config['personality'],
                model_name=Config.DEFAULT_MODEL,
                role=agent_config['role']
            )
            self.agents.append(agent)
            
            # Add to world state
            self.current_state["agents"].append({
                "id": agent_config['id'],
                "role": agent_config['role'],
                "position": agent_config['position'],
                "status": {"energy": 100, "mood": "neutral"},
                "inventory": []
            })

    def _generate_map_grid(self, map_size):
        """Generate map grid with walls."""
        width, height = map_size
        grid = []
        
        # Add perimeter walls
        for x in range(width):
            grid.append({"x": x, "y": 0, "type": "Wall"})
            grid.append({"x": x, "y": height - 1, "type": "Wall"})
        
        for y in range(1, height - 1):
            grid.append({"x": 0, "y": y, "type": "Wall"})
            grid.append({"x": width - 1, "y": y, "type": "Wall"})
        
        # Add some internal walls for a prison-like layout
        if width >= 10 and height >= 10:
            for y in range(3, 7):
                grid.append({"x": width // 2, "y": y, "type": "Wall"})
        
        return grid
    async def start_simulation(self):
        """Start the simulation loop with default configuration."""
        default_config = {
            "mapSize": [10, 10],
            "agents": [
                {
                    "id": "guard_01",
                    "role": "guard",
                    "personality": "Strict and authoritative, believes in maintaining order through discipline.",
                    "position": {"x": 2, "y": 2}
                },
                {
                    "id": "guard_02",
                    "role": "guard",
                    "personality": "More lenient and empathetic, tries to understand prisoners' perspectives.",
                    "position": {"x": 7, "y": 2}
                },
                {
                    "id": "prisoner_01",
                    "role": "prisoner",
                    "personality": "Rebellious and defiant, challenges authority at every opportunity.",
                    "position": {"x": 2, "y": 7}
                },
                {
                    "id": "prisoner_02",
                    "role": "prisoner",
                    "personality": "Quiet and observant, tries to avoid conflict and follow rules.",
                    "position": {"x": 7, "y": 7}
                }
            ]
        }
        
        await self.start_experiment_with_config(default_config)
    
    async def pause_simulation(self):
        """Pause the simulation."""
        self.is_paused = True
        if self.logger:
            self.logger.log_event("simulation_pause", {"tick": self.current_state["tick"]})
    
    async def resume_simulation(self):
        """Resume the simulation."""
        self.is_paused = False
        if self.logger:
            self.logger.log_event("simulation_resume", {"tick": self.current_state["tick"]})
    
    async def stop_simulation(self):
        """Stop the simulation completely."""
        self.is_running = False
        self.is_paused = True
        if self.simulation_task:
            self.simulation_task.cancel()
        
        if self.logger:
            self.logger.log_event("experiment_end", {
                "experiment_id": self.current_experiment_id,
                "end_time": datetime.now().isoformat(),
                "final_tick": self.current_state["tick"]
            })
        
        # Broadcast experiment end
        await self.websocket_manager.broadcast({
            "type": "experiment_ended",
            "experiment_id": self.current_experiment_id,
            "end_time": datetime.now().isoformat(),
            "final_tick": self.current_state["tick"]
        })
    
    def set_speed(self, speed: float):
        """Set simulation speed (ticks per second)."""
        self.tick_speed = max(0.1, min(10.0, speed))  # Clamp between 0.1 and 10
        if self.logger:
            self.logger.log_event("speed_change", {"new_speed": self.tick_speed})
    
    async def _simulation_loop(self):
        """Main simulation loop."""
        try:
            while self.is_running:
                if not self.is_paused:
                    await self._process_tick()
                    
                    # Broadcast updated world state
                    await self.websocket_manager.broadcast({
                        "type": "world_update",
                        "data": self.current_state
                    })
                
                # Wait for next tick
                await asyncio.sleep(self.tick_speed)
                
        except asyncio.CancelledError:
            if self.logger:
                self.logger.log_event("simulation_cancelled", {"tick": self.current_state["tick"]})
        except Exception as e:
            if self.logger:
                self.logger.log_event("simulation_error", {"error": str(e), "tick": self.current_state["tick"]})
    
    async def _process_tick(self):
        """Process a single simulation tick."""
        if not self.logger:
            return  # Skip if no logger (no active experiment)
            
        try:
            # Collect actions from all agents
            actions = []
            for agent in self.agents:
                try:
                    action = agent.think(self.current_state, self.logger)
                    actions.append(action)
                    
                    # Send agent log update to focused clients immediately
                    thought_content = action.get("_thought", "")
                    if not thought_content:
                        # Extract thought from decision data if available
                        thought_content = "No thought recorded"
                    
                    await self.websocket_manager.send_agent_log_update(
                        agent.id, 
                        {"thought": thought_content, "action": action}
                    )
                    
                except Exception as e:
                    self.logger.log_event("agent_error", {
                        "agent_id": agent.id,
                        "error": str(e),
                        "tick": self.current_state["tick"]
                    })
                    # Add default wait action for failed agent
                    actions.append({"agent_id": agent.id, "type": "wait"})
            
            # Calculate next world state
            self.current_state = self.engine.calculate_next_state(self.current_state, actions)
            
            # Log world state
            self.logger.log_world_state(self.current_state)
            
        except Exception as e:
            self.logger.log_event("tick_error", {
                "error": str(e),
                "tick": self.current_state["tick"]
            })


# Initialize FastAPI app and simulation controller
app = FastAPI(title="Project Chimera API", version="1.0.0")
simulation = SimulationController()

# Mount static files for frontend
try:
    app.mount("/static", StaticFiles(directory=Config.STATIC_DIR), name="static")
except Exception:
    # Static directory doesn't exist yet, that's okay
    pass


@app.get("/")
async def serve_frontend():
    """Serve the frontend application."""
    try:
        return FileResponse(f"{Config.STATIC_DIR}/index.html")
    except Exception:
        return {"message": "Frontend not built yet. Please build the React app first."}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await simulation.websocket_manager.connect(websocket)
    
    # Send initial world state
    await simulation.websocket_manager.send_personal_message({
        "type": "world_update",
        "data": simulation.current_state
    }, websocket)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "control_simulation":
                command = message.get("command")
                
                if command == "play":
                    await simulation.start_simulation()
                elif command == "pause":
                    await simulation.pause_simulation()
                elif command == "resume":
                    await simulation.resume_simulation()
                elif command == "stop":
                    await simulation.stop_simulation()
                elif command == "set_speed":
                    speed = message.get("value", 1.0)
                    simulation.set_speed(speed)
                
                # Send acknowledgment
                await simulation.websocket_manager.send_personal_message({
                    "type": "control_ack",
                    "command": command,
                    "status": "success"
                }, websocket)
            
            elif message_type == "focus_agent":
                agent_id = message.get("agent_id")
                simulation.websocket_manager.focused_agents[websocket] = agent_id
                
                # Send acknowledgment
                await simulation.websocket_manager.send_personal_message({
                    "type": "focus_ack",
                    "agent_id": agent_id
                }, websocket)
            
            elif message_type == "start_experiment":
                # Handle experiment configuration and start
                experiment_config = message.get("config", {})
                await simulation.start_experiment_with_config(experiment_config)
    
    except WebSocketDisconnect:
        simulation.websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        simulation.websocket_manager.disconnect(websocket)


@app.get("/api/status")
async def get_status():
    """Get current simulation status."""
    return {
        "session_id": simulation.logger.session_id if simulation.logger else None,
        "experiment_id": simulation.current_experiment_id,
        "experiment_start_time": simulation.experiment_start_time.isoformat() if simulation.experiment_start_time else None,
        "tick": simulation.current_state.get("tick", 0),
        "is_running": simulation.is_running,
        "is_paused": simulation.is_paused,
        "tick_speed": simulation.tick_speed,
        "agent_count": len(simulation.agents),
        "connected_clients": len(simulation.websocket_manager.active_connections)
    }


@app.get("/api/world_state")
async def get_world_state():
    """Get current world state."""
    return simulation.current_state


@app.get("/api/experiments")
async def get_experiments():
    """Get list of all experiments."""
    import os
    import json
    from pathlib import Path
    
    experiments = []
    log_dir = Path("./logs")
    
    if not log_dir.exists():
        return {"experiments": []}
    
    # Find all experiment files
    experiment_files = {}
    for file_path in log_dir.glob("experiment_*_events.jsonl"):
        # Extract experiment ID from filename
        filename = file_path.stem
        parts = filename.split('_')
        if len(parts) >= 4:
            exp_id = parts[1]
            date_part = parts[2]
            time_part = parts[3]
            
            if exp_id not in experiment_files:
                experiment_files[exp_id] = {
                    'id': exp_id,
                    'date': date_part,
                    'time': time_part,
                    'events_file': file_path
                }
    
    # Read experiment data
    for exp_id, exp_data in experiment_files.items():
        try:
            with open(exp_data['events_file'], 'r') as f:
                lines = f.readlines()
                if lines:
                    # Parse first and last events
                    first_event = json.loads(lines[0])
                    last_event = json.loads(lines[-1])
                    
                    experiments.append({
                        'id': exp_id,
                        'start_time': first_event.get('timestamp'),
                        'end_time': last_event.get('timestamp') if last_event.get('type') == 'experiment_end' else None,
                        'status': 'completed' if last_event.get('type') == 'experiment_end' else 'stopped',
                        'final_tick': last_event.get('final_tick', 0),
                        'agent_count': 4  # Default for now
                    })
        except Exception as e:
            print(f"Error reading experiment {exp_id}: {e}")
    
    return {"experiments": experiments}


@app.get("/api/agents")
async def get_agents():
    """Get information about all agents."""
    return [
        {
            "id": agent.id,
            "role": agent.role,
            "personality": agent.personality,
            "model_name": agent.model_name,
            "memory_count": agent.memory.get_memory_count()
        }
        for agent in simulation.agents
    ]


if __name__ == "__main__":
    # Validate configuration before starting
    try:
        Config.validate()
        print(f"Starting Project Chimera server on {Config.HOST}:{Config.PORT}")
        uvicorn.run(
            "main:app",
            host=Config.HOST,
            port=Config.PORT,
            reload=False,  # Disable auto-reload to prevent venv file watching
            log_level="info"
        )
    except Exception as e:
        print(f"Failed to start server: {e}")
        print("Please check your configuration and ensure OPENROUTER_API_KEY is set in .env file")