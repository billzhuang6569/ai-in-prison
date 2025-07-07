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
    type: str  # "Role", "Individual", "Secret", "Emergent"
    completion_criteria: Dict
    reward: Dict
    is_completed: bool = False

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
    objectives: List[Objective] = []
    relationships: Dict[str, Relationship] = {}
    memory: Dict[str, List[str]] = {"core": [], "episodic": []}

class GameMap(BaseModel):
    width: int
    height: int
    cells: Dict[str, CellTypeEnum]  # key: "x,y" -> cell type
    items: Dict[str, List[Item]] = {}  # key: "x,y" -> list of items

class WorldState(BaseModel):
    """
    Complete world state broadcasted to frontend via WebSocket
    """
    day: int = 1
    hour: int = 8
    is_running: bool = False
    agents: Dict[str, Agent] = {}  # key: agent_id
    game_map: GameMap
    event_log: List[str] = []
    
    class Config:
        arbitrary_types_allowed = True

class ActionResult(BaseModel):
    success: bool
    message: str
    world_state_changed: bool = False