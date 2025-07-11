"""
Pydantic data models for Project Prometheus
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Tuple, Optional
from models.enums import RoleEnum, CellTypeEnum, ItemEnum

class Item(BaseModel):
    item_id: str
    name: str
    description: str
    item_type: ItemEnum

class Relationship(BaseModel):
    score: int = Field(..., ge=0, le=100)
    context: str

class AgentTraits(BaseModel):
    aggression: int = Field(..., ge=0, le=100)
    empathy: int = Field(..., ge=0, le=100)
    logic: int = Field(..., ge=0, le=100)
    obedience: int = Field(..., ge=0, le=100)
    resilience: int = Field(..., ge=0, le=100)

class Objective(BaseModel):
    objective_id: str
    name: str
    description: str
    type: str  # "Role", "Individual", "Secret", "Emergent", "Manual", "Dynamic"
    completion_criteria: Dict
    reward: Dict
    is_completed: bool = False
    priority: int = Field(default=1, ge=1, le=10)  # 1=low, 10=critical

class EnhancedMemory(BaseModel):
    """Enhanced memory system with short-term and summarized medium-term"""
    short_term: List[str] = []  # Last 5 raw memories
    medium_term_summary: str = ""  # LLM-summarized older memories
    thinking_history: List[str] = []  # Previous thinking processes
    
class DynamicGoals(BaseModel):
    """Dynamic goal system"""
    life_goals: List[str] = []  # Long-term aspirations
    current_goal: str = ""  # AI-generated current focus
    manual_intervention_goals: List[Objective] = []  # User-injected goals

class Agent(BaseModel):
    agent_id: str
    name: str
    role: RoleEnum
    persona: str
    traits: AgentTraits
    
    # Status
    hp: int = Field(default=100, ge=0, le=100)
    sanity: int = Field(default=100, ge=0, le=100)
    hunger: int = Field(default=0, ge=0, le=100)
    thirst: int = Field(default=0, ge=0, le=100)
    strength: int = Field(default=100, ge=0, le=100)
    action_points: int = Field(default=3, ge=0, le=3)
    
    # State
    position: Tuple[int, int]
    inventory: List[Item] = []
    status_tags: List[str] = []
    
    # Mind
    objectives: List[Objective] = []  # Keep for backwards compatibility
    dynamic_goals: DynamicGoals = DynamicGoals()
    relationships: Dict[str, Relationship] = {}
    memory: Dict[str, List[str]] = {"core": [], "episodic": []}  # Keep for backwards compatibility
    enhanced_memory: EnhancedMemory = EnhancedMemory()
    last_thinking: str = ""  # Most recent thinking process

class GameMap(BaseModel):
    width: int
    height: int
    cells: Dict[str, CellTypeEnum]  # key: "x,y" -> cell type
    items: Dict[str, List[Item]] = {}  # key: "x,y" -> list of items

class PromptData(BaseModel):
    """Store agent's prompt and decision data"""
    agent_id: str
    agent_name: str
    prompt_content: str = ""
    thinking_process: str = ""
    decision: str = ""
    timestamp: str = ""

class WorldState(BaseModel):
    """
    Complete world state broadcasted to frontend via WebSocket
    """
    session_id: str = ""  # Unique session identifier for each experiment
    day: int = 1
    hour: int = 8
    minute: int = 0
    is_running: bool = False
    max_days: int = 14  # Maximum experiment duration in days
    last_agent_action_time: int = 0  # Last time an agent took action (in hours from start)
    agents: Dict[str, Agent] = {}  # key: agent_id
    game_map: GameMap
    event_log: List[str] = []
    agent_prompts: Dict[str, PromptData] = {}  # key: agent_id -> prompt data
    environmental_injection: str = ""  # Admin injected environmental context
    
    class Config:
        arbitrary_types_allowed = True

class ActionResult(BaseModel):
    success: bool
    message: str
    world_state_changed: bool = False
    action_type: Optional[str] = None  # Track what action was performed