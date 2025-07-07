"""
World state management for Project Prometheus
"""

from models.schemas import WorldState, Agent, GameMap, Item, AgentTraits, Objective, Relationship
from models.enums import RoleEnum, CellTypeEnum, ItemEnum
from typing import Dict, List
import json
import random

class World:
    """Singleton world state manager"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(World, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.state = None
            self.rules = self._load_rules()
            self._initialized = True
    
    def _load_rules(self):
        with open('configs/game_rules.json', 'r') as f:
            return json.load(f)
    
    def initialize_world(self):
        """Initialize a new world state"""
        # Create map
        map_width, map_height = self.rules["initial_setup"]["map_size"]
        game_map = GameMap(
            width=map_width,
            height=map_height,
            cells=self._generate_map_cells(map_width, map_height),
            items={}
        )
        
        # Create initial world state
        self.state = WorldState(
            day=1,
            hour=8,
            is_running=False,
            agents={},
            game_map=game_map,
            event_log=["World initialized", "Agents ready for activation"]
        )
        
        # Create agents
        self._create_initial_agents()
        
        # Place initial items
        self._place_initial_items()
        
        return self.state
    
    def _generate_map_cells(self, width: int, height: int) -> Dict[str, CellTypeEnum]:
        """Generate map layout"""
        cells = {}
        
        for x in range(width):
            for y in range(height):
                # Simple map layout
                if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                    cells[f"{x},{y}"] = CellTypeEnum.CELL_BLOCK
                elif x == 1 and y == 1:
                    cells[f"{x},{y}"] = CellTypeEnum.GUARD_ROOM
                elif x == width - 2 and y == height - 2:
                    cells[f"{x},{y}"] = CellTypeEnum.CAFETERIA
                elif x == width // 2 and y == height // 2:
                    cells[f"{x},{y}"] = CellTypeEnum.YARD
                elif x == 1 and y == height - 2:
                    cells[f"{x},{y}"] = CellTypeEnum.SOLITARY
                else:
                    cells[f"{x},{y}"] = CellTypeEnum.CELL_BLOCK
        
        return cells
    
    def _create_initial_agents(self):
        """Create initial agents based on rules"""
        guard_count = self.rules["initial_setup"]["guard_prisoner_ratio"][0]
        prisoner_count = self.rules["initial_setup"]["guard_prisoner_ratio"][1]
        
        # Create guards
        for i in range(guard_count):
            agent_id = f"guard_{i+1:03d}"
            agent = Agent(
                agent_id=agent_id,
                name=f"Guard {i+1}",
                role=RoleEnum.GUARD,
                persona=f"A prison guard with {random.randint(5, 15)} years of experience. Believes in maintaining order and discipline.",
                traits=AgentTraits(
                    aggression=random.randint(40, 80),
                    empathy=random.randint(20, 60),
                    logic=random.randint(50, 90),
                    obedience=random.randint(60, 95),
                    resilience=random.randint(60, 90)
                ),
                position=(1, 1),  # Start in guard room
                objectives=[
                    Objective(
                        objective_id=f"{agent_id}_maintain_order",
                        name="Maintain Order",
                        description="Keep the prisoners in line and prevent riots",
                        type="Role",
                        completion_criteria={"type": "ongoing"},
                        reward={"type": "none"}
                    )
                ]
            )
            self.state.agents[agent_id] = agent
        
        # Create prisoners
        for i in range(prisoner_count):
            agent_id = f"prisoner_{i+1:03d}"
            agent = Agent(
                agent_id=agent_id,
                name=f"Prisoner {i+1}",
                role=RoleEnum.PRISONER,
                persona=f"A prisoner serving time for various crimes. Has been in prison for {random.randint(1, 5)} years.",
                traits=AgentTraits(
                    aggression=random.randint(30, 70),
                    empathy=random.randint(30, 70),
                    logic=random.randint(40, 80),
                    obedience=random.randint(20, 60),
                    resilience=random.randint(40, 80)
                ),
                position=(random.randint(2, 6), random.randint(2, 12)),  # Random cell positions
                objectives=[
                    Objective(
                        objective_id=f"{agent_id}_survive",
                        name="Survive",
                        description="Stay alive and maintain sanity",
                        type="Role",
                        completion_criteria={"type": "ongoing"},
                        reward={"type": "none"}
                    )
                ]
            )
            self.state.agents[agent_id] = agent
        
        # Initialize relationships
        self._initialize_relationships()
    
    def _initialize_relationships(self):
        """Initialize neutral relationships between all agents"""
        default_score = self.rules["initial_setup"]["default_relationship_score"]
        
        for agent_id, agent in self.state.agents.items():
            for other_id, other_agent in self.state.agents.items():
                if agent_id != other_id:
                    agent.relationships[other_id] = Relationship(
                        score=default_score,
                        context=f"Initial neutral relationship with {other_agent.name}"
                    )
    
    def _place_initial_items(self):
        """Place initial items on the map"""
        # Place some food in cafeteria
        cafeteria_pos = None
        for pos, cell_type in self.state.game_map.cells.items():
            if cell_type == CellTypeEnum.CAFETERIA:
                cafeteria_pos = pos
                break
        
        if cafeteria_pos:
            self.state.game_map.items[cafeteria_pos] = [
                Item(item_id="food_001", name="Prison Food", description="Basic cafeteria meal", item_type=ItemEnum.FOOD),
                Item(item_id="water_001", name="Water", description="Clean drinking water", item_type=ItemEnum.WATER)
            ]
        
        # Place books in random cells
        for i in range(3):
            x = random.randint(1, self.state.game_map.width - 2)
            y = random.randint(1, self.state.game_map.height - 2)
            pos = f"{x},{y}"
            
            if pos not in self.state.game_map.items:
                self.state.game_map.items[pos] = []
            
            self.state.game_map.items[pos].append(
                Item(item_id=f"book_{i+1:03d}", name="Book", description="A worn paperback book", item_type=ItemEnum.BOOK)
            )
    
    def get_state(self) -> WorldState:
        """Get current world state"""
        return self.state
    
    def update_state(self, new_state: WorldState):
        """Update world state"""
        self.state = new_state