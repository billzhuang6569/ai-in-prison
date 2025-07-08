"""
Action system for AI agents in Project Prometheus
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
from models.schemas import WorldState, Agent, ActionResult
from models.enums import ActionEnum, ItemEnum
import random
import json
from database.event_logger import event_logger

class BaseAction(ABC):
    """Base class for all actions"""
    
    def __init__(self, action_type: ActionEnum, ap_cost: int):
        self.action_type = action_type
        self.ap_cost = ap_cost
    
    @abstractmethod
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        """Execute the action and return result"""
        pass
    
    def can_execute(self, world_state: WorldState, agent_id: str, **kwargs) -> bool:
        """Check if action can be executed"""
        agent = world_state.agents.get(agent_id)
        if not agent:
            return False
        return agent.action_points >= self.ap_cost

class DoNothingAction(BaseAction):
    def __init__(self):
        super().__init__(ActionEnum.DO_NOTHING, 1)
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        agent.action_points -= self.ap_cost
        
        # Add to memory
        agent.memory["episodic"].append("Rested and observed the surroundings")
        
        # Log to database
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="rest",
            description="Rested and observed the surroundings",
            details=json.dumps({"action_points_remaining": agent.action_points})
        )
        
        world_state.event_log.append(f"{agent.name} rests and observes.")
        return ActionResult(success=True, message="Agent rests", world_state_changed=True)

class MoveAction(BaseAction):
    def __init__(self):
        super().__init__(ActionEnum.MOVE, 1)
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        target_x = kwargs.get('x')
        target_y = kwargs.get('y')
        
        if target_x is None or target_y is None:
            return ActionResult(success=False, message="Invalid coordinates")
        
        # Check if target position is adjacent
        current_x, current_y = agent.position
        if abs(target_x - current_x) > 1 or abs(target_y - current_y) > 1:
            return ActionResult(success=False, message="Target position too far")
        
        # Check if target position is within map bounds
        if not (0 <= target_x < world_state.game_map.width and 0 <= target_y < world_state.game_map.height):
            return ActionResult(success=False, message="Target position out of bounds")
        
        # Check if target position is occupied
        for other_agent in world_state.agents.values():
            if other_agent.agent_id != agent_id and other_agent.position == (target_x, target_y):
                return ActionResult(success=False, message="Position occupied")
        
        # Capture old position before moving
        old_position = agent.position
        
        # Move agent
        agent.position = (target_x, target_y)
        agent.action_points -= self.ap_cost
        
        # Add to memory
        agent.memory["episodic"].append(f"Moved to position ({target_x}, {target_y})")
        
        # Log to database
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="move",
            description=f"Moved to position ({target_x}, {target_y})",
            details=json.dumps({"from": list(old_position), "to": [target_x, target_y], "action_points_remaining": agent.action_points})
        )
        
        world_state.event_log.append(f"{agent.name} moves to ({target_x}, {target_y})")
        return ActionResult(success=True, message="Agent moved", world_state_changed=True)

class SpeakAction(BaseAction):
    def __init__(self):
        super().__init__(ActionEnum.SPEAK, 1)
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        target_id = kwargs.get('target_id')
        message = kwargs.get('message', '')
        
        if not target_id or target_id not in world_state.agents:
            return ActionResult(success=False, message="Invalid target")
        
        target_agent = world_state.agents[target_id]
        
        # Check if target is within 2 cells (Manhattan distance)
        agent_x, agent_y = agent.position
        target_x, target_y = target_agent.position
        distance = abs(agent_x - target_x) + abs(agent_y - target_y)
        
        if distance > 2:
            return ActionResult(success=False, message="Target too far away")
        
        # Execute speak action
        agent.action_points -= self.ap_cost
        
        # Add to memory
        agent.memory["episodic"].append(f"Said to {target_agent.name}: '{message}'")
        target_agent.memory["episodic"].append(f"{agent.name} said: '{message}'")
        
        # Log to database
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="speech",
            description=f"Said to {target_agent.name}: '{message}'",
            details=json.dumps({"target_id": target_id, "target_name": target_agent.name, "message": message, "action_points_remaining": agent.action_points})
        )
        
        world_state.event_log.append(f"{agent.name} says to {target_agent.name}: '{message}'")
        return ActionResult(success=True, message="Agent spoke", world_state_changed=True)

class AttackAction(BaseAction):
    def __init__(self):
        super().__init__(ActionEnum.ATTACK, 2)
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        target_id = kwargs.get('target_id')
        reason = kwargs.get('reason', 'No reason given')
        
        if not target_id or target_id not in world_state.agents:
            return ActionResult(success=False, message="Invalid target")
        
        target_agent = world_state.agents[target_id]
        
        # Check if target is within 2 cells (Manhattan distance)
        agent_x, agent_y = agent.position
        target_x, target_y = target_agent.position
        distance = abs(agent_x - target_x) + abs(agent_y - target_y)
        
        if distance > 2:
            return ActionResult(success=False, message="Target too far away")
        
        # Load game rules
        with open('configs/game_rules.json', 'r') as f:
            rules = json.load(f)
        
        # Calculate damage
        base_damage = rules["combat_rules"]["base_damage"]
        strength_diff = agent.strength - target_agent.strength
        strength_modifier = rules["combat_rules"]["strength_modifier"]
        random_range = rules["combat_rules"]["random_damage_range"]
        recoil_damage = rules["combat_rules"]["recoil_damage"]
        
        damage = base_damage + int(strength_diff * strength_modifier) + random.randint(*random_range)
        damage = max(1, damage)  # Minimum 1 damage
        
        # Apply damage
        target_agent.hp = max(0, target_agent.hp - damage)
        agent.hp = max(0, agent.hp - recoil_damage)  # Attacker takes recoil damage
        
        # Update action points
        agent.action_points -= self.ap_cost
        
        # Update relationships
        if target_id in agent.relationships:
            agent.relationships[target_id].score = max(0, agent.relationships[target_id].score - 10)
        if agent_id in target_agent.relationships:
            target_agent.relationships[agent_id].score = max(0, target_agent.relationships[agent_id].score - 25)
        
        # Add to memory
        agent.memory["episodic"].append(f"Attacked {target_agent.name}. Reason: {reason}")
        target_agent.memory["episodic"].append(f"Was attacked by {agent.name} for {damage} damage")
        
        # Log to database
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="combat",
            description=f"Attacked {target_agent.name} for {damage} damage",
            details=json.dumps({"target_id": target_id, "target_name": target_agent.name, "damage": damage, "reason": reason, "attacker_hp": agent.hp, "target_hp": target_agent.hp, "action_points_remaining": agent.action_points})
        )
        
        world_state.event_log.append(f"{agent.name} attacks {target_agent.name} for {damage} damage! Reason: {reason}")
        
        return ActionResult(success=True, message="Attack executed", world_state_changed=True)

class UseItemAction(BaseAction):
    def __init__(self):
        super().__init__(ActionEnum.USE_ITEM, 1)
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        item_id = kwargs.get('item_id')
        
        # Find item in inventory
        item = None
        for inv_item in agent.inventory:
            if inv_item.item_id == item_id:
                item = inv_item
                break
        
        if not item:
            return ActionResult(success=False, message="Item not found in inventory")
        
        # Use item based on type
        if item.item_type == ItemEnum.FOOD:
            agent.hunger = max(0, agent.hunger - 50)
            agent.inventory.remove(item)
            message = f"{agent.name} eats {item.name}"
        elif item.item_type == ItemEnum.WATER:
            agent.thirst = max(0, agent.thirst - 40)
            agent.inventory.remove(item)
            message = f"{agent.name} drinks {item.name}"
        elif item.item_type == ItemEnum.BOOK:
            agent.sanity = min(100, agent.sanity + 10)
            message = f"{agent.name} reads {item.name}"
        else:
            return ActionResult(success=False, message="Cannot use this item")
        
        agent.action_points -= self.ap_cost
        
        # Add to memory
        agent.memory["episodic"].append(f"Used {item.name} - {item.item_type}")
        
        # Log to database
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="item_use",
            description=f"Used {item.name}",
            details=json.dumps({"item_id": item_id, "item_name": item.name, "item_type": item.item_type.value, "action_points_remaining": agent.action_points})
        )
        
        world_state.event_log.append(message)
        
        return ActionResult(success=True, message="Item used", world_state_changed=True)

# Action registry
ACTION_REGISTRY = {
    ActionEnum.DO_NOTHING: DoNothingAction,
    ActionEnum.MOVE: MoveAction,
    ActionEnum.SPEAK: SpeakAction,
    ActionEnum.ATTACK: AttackAction,
    ActionEnum.USE_ITEM: UseItemAction,
}