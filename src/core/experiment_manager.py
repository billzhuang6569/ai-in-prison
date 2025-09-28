"""
Experiment Manager for Project Chimera

This module provides experiment lifecycle management, separating experiment
configuration and initialization from simulation control.
"""

from typing import Dict, List, Any, Tuple
from datetime import datetime
import uuid

from src.agents.agent import AIAgent
from src.core.inventory_system import ItemManager
from config import Config


class ExperimentManager:
    """
    Manages individual experiment instances with their configuration,
    initial state generation, and metadata tracking.
    
    This class follows the Single Responsibility Principle by focusing
    solely on experiment management, separate from simulation control.
    """
    
    def __init__(self, experiment_config: Dict[str, Any]):
        """
        Initialize experiment manager with configuration.
        
        Args:
            experiment_config: Dictionary containing experiment parameters
        """
        self.config = experiment_config
        self.experiment_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now()
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """
        Validate experiment configuration parameters.
        
        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = ['mapSize', 'agents']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate map size
        map_size = self.config['mapSize']
        if not isinstance(map_size, list) or len(map_size) != 2:
            raise ValueError("mapSize must be a list of two integers [width, height]")
        
        if map_size[0] < 5 or map_size[1] < 5:
            raise ValueError("Map size must be at least 5x5")
        
        # Validate agents
        agents = self.config['agents']
        if not isinstance(agents, list) or len(agents) == 0:
            raise ValueError("At least one agent must be specified")
        
        for i, agent in enumerate(agents):
            required_agent_fields = ['id', 'role', 'personality', 'position']
            for field in required_agent_fields:
                if field not in agent:
                    raise ValueError(f"Agent {i} missing required field: {field}")
    
    def create_initial_state(self) -> Tuple[Dict[str, Any], List[AIAgent]]:
        """
        Generate initial world state and agent instances based on configuration.
        
        Returns:
            Tuple of (world_state, agents_list)
        """
        # Create world state
        world_state = {
            "tick": 0,
            "map": {
                "size": self.config['mapSize'],
                "grid": self._generate_map_grid(self.config['mapSize'])
            },
            "agents": [],
            "objects": []
        }
        
        # Create agent instances
        agents = []
        for agent_config in self.config['agents']:
            agent = AIAgent(
                agent_id=agent_config['id'],
                personality=agent_config['personality'],
                model_name=Config.DEFAULT_MODEL,
                role=agent_config['role']
            )
            agents.append(agent)
            
            # Add agent to world state
            world_state["agents"].append({
                "id": agent_config['id'],
                "role": agent_config['role'],
                "position": agent_config['position'].copy(),
                "status": {"energy": 100, "mood": "neutral"},
                "inventory": []
            })
        
        # Add sample items if configured
        if self.config.get('addSampleItems', True):
            self._add_sample_items(world_state)
        
        return world_state, agents
    
    def _generate_map_grid(self, map_size: List[int]) -> List[Dict[str, Any]]:
        """
        Generate map grid with walls based on size.
        
        Args:
            map_size: [width, height] of the map
            
        Returns:
            List of grid objects (walls, etc.)
        """
        width, height = map_size
        grid = []
        
        # Add perimeter walls
        for x in range(width):
            grid.append({"x": x, "y": 0, "type": "Wall"})
            grid.append({"x": x, "y": height - 1, "type": "Wall"})
        
        for y in range(1, height - 1):
            grid.append({"x": 0, "y": y, "type": "Wall"})
            grid.append({"x": width - 1, "y": y, "type": "Wall"})
        
        # Add internal walls for prison-like layout
        if width >= 10 and height >= 10:
            # Central dividing wall
            for y in range(3, min(7, height - 3)):
                grid.append({"x": width // 2, "y": y, "type": "Wall"})
        
        # Add custom walls if specified in config
        custom_walls = self.config.get('customWalls', [])
        for wall in custom_walls:
            if self._is_valid_position(wall, width, height):
                grid.append({"x": wall['x'], "y": wall['y'], "type": "Wall"})
        
        return grid
    
    def _add_sample_items(self, world_state: Dict[str, Any]) -> None:
        """
        Add sample items to the world for testing purposes.
        
        Args:
            world_state: World state to modify
        """
        item_manager = ItemManager()
        width, height = world_state["map"]["size"]
        
        # Add some food rations in safe locations
        if width >= 6 and height >= 6:
            food1 = item_manager.create_item("Food", {"x": width // 3, "y": height // 3})
            food2 = item_manager.create_item("Food", {"x": 2 * width // 3, "y": 2 * height // 3})
            world_state["objects"].extend([food1, food2])
        
        # Add a note
        if width >= 8 and height >= 8:
            note = item_manager.create_item(
                "Readable", 
                {"x": width - 3, "y": height - 3}, 
                {"content": "Meet me at the cafeteria at midnight"}
            )
            world_state["objects"].append(note)
        
        # Add a medkit
        if width >= 5 and height >= 5:
            medkit = item_manager.create_item("Consumable", {"x": 2, "y": 2})
            world_state["objects"].append(medkit)
    
    def _is_valid_position(self, pos: Dict[str, int], width: int, height: int) -> bool:
        """
        Check if a position is valid within map bounds.
        
        Args:
            pos: Position dictionary with 'x' and 'y' keys
            width: Map width
            height: Map height
            
        Returns:
            True if position is valid
        """
        return (0 <= pos.get('x', -1) < width and 
                0 <= pos.get('y', -1) < height)
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get experiment metadata.
        
        Returns:
            Dictionary with experiment metadata
        """
        return {
            "experiment_id": self.experiment_id,
            "start_time": self.start_time.isoformat(),
            "config": self.config.copy(),
            "agent_count": len(self.config['agents']),
            "map_size": self.config['mapSize']
        }
    
    def get_session_id(self) -> str:
        """
        Generate a unique session ID for logging purposes.
        
        Returns:
            Formatted session ID string
        """
        return f"experiment_{self.experiment_id}_{self.start_time.strftime('%Y%m%d_%H%M%S')}"