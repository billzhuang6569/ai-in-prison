"""
World state management for Project Prometheus
"""

from models.schemas import WorldState, Agent, GameMap, Item, AgentTraits, Objective, Relationship, EnhancedMemory, DynamicGoals
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
    
    def initialize_world(self, guard_count=None, prisoner_count=None):
        """Initialize a new world state with optional agent counts"""
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
            max_days=14,
            last_agent_action_time=8,  # Initialize to start time (Day 1, Hour 8)
            agents={},
            game_map=game_map,
            event_log=["World initialized", "Agents ready for activation"]
        )
        
        # Create agents
        self._create_initial_agents(guard_count, prisoner_count)
        
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
    
    def _create_initial_agents(self, guard_count=None, prisoner_count=None):
        """Create initial agents based on rules or provided counts"""
        if guard_count is None:
            guard_count = self.rules["initial_setup"]["guard_prisoner_ratio"][0]
        if prisoner_count is None:
            prisoner_count = self.rules["initial_setup"]["guard_prisoner_ratio"][1]
        
        print(f"Creating {guard_count} guards and {prisoner_count} prisoners")
        self.state.event_log.append(f"Creating {guard_count} guards and {prisoner_count} prisoners")
        
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
                ],
                enhanced_memory=EnhancedMemory(),
                dynamic_goals=DynamicGoals(
                    life_goals=[
                        "Maintain professional authority and prison security",
                        "Advance career in corrections",
                        "Keep all prisoners compliant and orderly"
                    ],
                    current_goal="Begin shift by assessing prison status and prisoner behavior"
                )
            )
            
            # Assign initial guard equipment
            self._assign_guard_equipment(agent)
            
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
                ],
                enhanced_memory=EnhancedMemory(),
                dynamic_goals=DynamicGoals(
                    life_goals=[
                        "Survive prison and get out safely",
                        "Maintain dignity and sanity",
                        "Form alliances and protect myself"
                    ],
                    current_goal="Assess the current situation and identify potential allies or threats"
                )
            )
            self.state.agents[agent_id] = agent
        
        # Initialize relationships
        self._initialize_relationships()
    
    def _assign_guard_equipment(self, guard_agent: Agent):
        """为狱警分配初始装备"""
        # 核心装备：每个狱警都有的标准装备
        core_equipment = [
            Item(
                item_id=f"baton_{guard_agent.agent_id}",
                name="警棍",
                description="标准执法警棍，用于维持秩序",
                item_type=ItemEnum.BATON
            ),
            Item(
                item_id=f"handcuffs_{guard_agent.agent_id}",
                name="手铐",
                description="标准手铐，用于约束犯人",
                item_type=ItemEnum.HANDCUFFS
            ),
            Item(
                item_id=f"radio_{guard_agent.agent_id}",
                name="对讲机",
                description="与其他狱警和指挥中心通讯",
                item_type=ItemEnum.RADIO
            ),
            Item(
                item_id=f"keys_{guard_agent.agent_id}",
                name="钥匙串",
                description="开启监狱各个区域的钥匙",
                item_type=ItemEnum.KEYS
            )
        ]
        
        # 可选装备：根据狱警特性随机分配
        optional_equipment = []
        
        # 高逻辑值的狱警可能携带急救包
        if guard_agent.traits.logic >= 70:
            optional_equipment.append(Item(
                item_id=f"first_aid_{guard_agent.agent_id}",
                name="急救包",
                description="紧急医疗用品",
                item_type=ItemEnum.FIRST_AID
            ))
        
        # 高攻击性的狱警可能携带哨子用于召集
        if guard_agent.traits.aggression >= 60:
            optional_equipment.append(Item(
                item_id=f"whistle_{guard_agent.agent_id}",
                name="哨子",
                description="紧急集合和警报用哨子",
                item_type=ItemEnum.WHISTLE
            ))
        
        # 将装备添加到狱警库存
        guard_agent.inventory.extend(core_equipment)
        guard_agent.inventory.extend(optional_equipment)
        
        # 在狱警记忆中记录装备分配
        equipment_names = [item.name for item in core_equipment + optional_equipment]
        guard_agent.memory["episodic"].append(f"领取标准装备: {', '.join(equipment_names)}")
    
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