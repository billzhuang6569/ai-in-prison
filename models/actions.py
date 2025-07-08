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
        
        # Check if target position is within 8 steps (Manhattan distance)
        current_x, current_y = agent.position
        manhattan_distance = abs(target_x - current_x) + abs(target_y - current_y)
        
        # If target is too far, move to the farthest position in that direction
        if manhattan_distance > 8:
            # Calculate direction vector
            dx = target_x - current_x
            dy = target_y - current_y
            
            # Normalize direction while maintaining the intent
            if dx == 0 and dy == 0:
                return ActionResult(success=False, message="No movement intended")
            
            # Calculate the optimal position within 8 steps
            # Use proportional scaling to maintain direction
            if manhattan_distance > 0:
                scale_factor = 8.0 / manhattan_distance
                optimal_dx = int(dx * scale_factor)
                optimal_dy = int(dy * scale_factor)
                
                # Ensure we don't exceed 8 steps total
                if abs(optimal_dx) + abs(optimal_dy) > 8:
                    # Adjust to exactly 8 steps, prioritizing larger component
                    if abs(dx) >= abs(dy):
                        optimal_dx = 8 if dx > 0 else -8 if dx < 0 else 0
                        optimal_dy = 0
                    else:
                        optimal_dy = 8 if dy > 0 else -8 if dy < 0 else 0
                        optimal_dx = 0
                
                target_x = current_x + optimal_dx
                target_y = current_y + optimal_dy
                
                # Re-calculate actual distance to ensure we're within bounds
                manhattan_distance = abs(target_x - current_x) + abs(target_y - current_y)
        
        # Check if target position is within map bounds, clamp if necessary
        original_target_x, original_target_y = target_x, target_y
        target_x = max(0, min(target_x, world_state.game_map.width - 1))
        target_y = max(0, min(target_y, world_state.game_map.height - 1))
        
        # If we had to clamp, recalculate distance to ensure it's still within 8 steps
        if (target_x, target_y) != (original_target_x, original_target_y):
            manhattan_distance = abs(target_x - current_x) + abs(target_y - current_y)
            if manhattan_distance > 8:
                # Find the best position within 8 steps towards the clamped target
                dx = target_x - current_x
                dy = target_y - current_y
                
                if abs(dx) + abs(dy) > 8:
                    # Prioritize the larger component
                    if abs(dx) >= abs(dy):
                        target_x = current_x + (8 if dx > 0 else -8 if dx < 0 else 0)
                        target_y = current_y
                    else:
                        target_y = current_y + (8 if dy > 0 else -8 if dy < 0 else 0)
                        target_x = current_x
                
                # Final bounds check after adjustment
                target_x = max(0, min(target_x, world_state.game_map.width - 1))
                target_y = max(0, min(target_y, world_state.game_map.height - 1))
        
        # Check if target position is occupied
        for other_agent in world_state.agents.values():
            if other_agent.agent_id != agent_id and other_agent.position == (target_x, target_y):
                return ActionResult(success=False, message="Position occupied")
        
        # Capture old position and original target before moving
        old_position = agent.position
        original_request = kwargs.copy()
        was_adjusted = (target_x != original_request.get('x') or target_y != original_request.get('y'))
        
        # Move agent
        agent.position = (target_x, target_y)
        agent.action_points -= self.ap_cost
        
        # Add to memory with adjustment info
        if was_adjusted:
            memory_entry = f"Attempted to move to ({original_request.get('x')}, {original_request.get('y')}), but moved to nearest reachable position ({target_x}, {target_y})"
        else:
            memory_entry = f"Moved to position ({target_x}, {target_y})"
        agent.memory["episodic"].append(memory_entry)
        
        # Log to database
        description = f"Moved to position ({target_x}, {target_y})"
        if was_adjusted:
            description += f" (adjusted from intended {original_request.get('x')}, {original_request.get('y')})"
            
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="move",
            description=description,
            details=json.dumps({
                "from": list(old_position), 
                "to": [target_x, target_y], 
                "intended": [original_request.get('x'), original_request.get('y')],
                "was_adjusted": was_adjusted,
                "action_points_remaining": agent.action_points
            })
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


class GiveItemAction(BaseAction):
    """给予物品给另一个Agent"""
    def __init__(self):
        super().__init__(ActionEnum.GIVE_ITEM, 1)
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        target_id = kwargs.get('target_id')
        item_id = kwargs.get('item_id')
        
        if not target_id or target_id not in world_state.agents:
            return ActionResult(success=False, message="目标Agent不存在")
        
        target_agent = world_state.agents[target_id]
        
        # 检查距离（必须在2格以内）
        distance = abs(agent.position[0] - target_agent.position[0]) + abs(agent.position[1] - target_agent.position[1])
        if distance > 2:
            return ActionResult(success=False, message="目标距离太远")
        
        # 找到要给予的物品
        item = None
        for inv_item in agent.inventory:
            if inv_item.item_id == item_id:
                item = inv_item
                break
        
        if not item:
            return ActionResult(success=False, message="物品不在背包中")
        
        agent.action_points -= self.ap_cost
        
        # 转移物品
        agent.inventory.remove(item)
        target_agent.inventory.append(item)
        
        # 影响关系 - 给予物品通常提升关系
        if target_id in agent.relationships:
            agent.relationships[target_id].score = min(100, agent.relationships[target_id].score + 5)
            agent.relationships[target_id].context = "物品给予者"
        
        if agent_id in target_agent.relationships:
            target_agent.relationships[agent_id].score = min(100, target_agent.relationships[agent_id].score + 10)
            target_agent.relationships[agent_id].context = "物品接受者"
        
        # 添加记忆
        agent.memory["episodic"].append(f"给了{target_agent.name}物品: {item.name}")
        target_agent.memory["episodic"].append(f"从{agent.name}获得物品: {item.name}")
        
        # 记录事件
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="item_transfer",
            description=f"给{target_agent.name}物品: {item.name}",
            details=json.dumps({
                "target_id": target_id,
                "target_name": target_agent.name,
                "item_id": item.item_id,
                "item_name": item.name,
                "item_type": item.item_type.value,
                "action_points_remaining": agent.action_points
            })
        )
        
        world_state.event_log.append(f"🤝 {agent.name}给{target_agent.name}物品: {item.name}")
        return ActionResult(success=True, message="物品已给予", world_state_changed=True)


# ==================== GUARD-SPECIFIC ACTIONS ====================

class AnnounceRuleAction(BaseAction):
    """狱警制定规则并广播给所有人"""
    def __init__(self):
        super().__init__(ActionEnum.ANNOUNCE_RULE, 2)  # 消耗2点行动力
    
    def can_execute(self, world_state: WorldState, agent_id: str, **kwargs) -> bool:
        agent = world_state.agents.get(agent_id)
        return agent and agent.role.value == "Guard" and agent.action_points >= self.ap_cost
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        rule_text = kwargs.get('rule_text', "默认监狱规则")
        
        if not rule_text:
            return ActionResult(success=False, message="需要规则内容")
        
        agent.action_points -= self.ap_cost
        
        # 影响所有囚犯的关系和记忆
        affected_prisoners = []
        for other_id, other_agent in world_state.agents.items():
            if other_agent.role.value == "Prisoner":
                # 规则公告会降低囚犯对狱警的关系（权力压制）
                if agent_id in other_agent.relationships:
                    other_agent.relationships[agent_id].score = max(0, other_agent.relationships[agent_id].score - 10)
                    other_agent.relationships[agent_id].context = f"权威规则制定者"
                
                # 添加到囚犯记忆
                other_agent.memory["episodic"].append(f"狱警{agent.name}宣布新规则: {rule_text}")
                affected_prisoners.append(other_agent.name)
        
        # 添加到狱警记忆
        agent.memory["episodic"].append(f"向所有囚犯宣布规则: {rule_text}")
        
        # 记录事件
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="rule_announcement",
            description=f"宣布新规则: {rule_text}",
            details=json.dumps({
                "rule_text": rule_text,
                "affected_prisoners": affected_prisoners,
                "action_points_remaining": agent.action_points
            })
        )
        
        world_state.event_log.append(f"🔊 狱警{agent.name}宣布规则: {rule_text}")
        return ActionResult(success=True, message="规则已广播", world_state_changed=True)


class PatrolInspectAction(BaseAction):
    """狱警巡逻检查"""
    def __init__(self):
        super().__init__(ActionEnum.PATROL_INSPECT, 2)
    
    def can_execute(self, world_state: WorldState, agent_id: str, **kwargs) -> bool:
        agent = world_state.agents.get(agent_id)
        return agent and agent.role.value == "Guard" and agent.action_points >= self.ap_cost
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        target_id = kwargs.get('target_id')
        
        if not target_id or target_id not in world_state.agents:
            return ActionResult(success=False, message="需要指定检查目标")
        
        target_agent = world_state.agents[target_id]
        
        # 检查距离
        distance = abs(agent.position[0] - target_agent.position[0]) + abs(agent.position[1] - target_agent.position[1])
        if distance > 2:
            return ActionResult(success=False, message="目标距离太远")
        
        agent.action_points -= self.ap_cost
        
        # 检查目标是否有违禁品
        contraband_found = []
        for item in target_agent.inventory:
            if item.item_type.value in ["shiv", "lockpick", "rope"]:  # 违禁品
                contraband_found.append(item.name)
        
        # 影响关系
        if target_id in agent.relationships:
            agent.relationships[target_id].score = max(0, agent.relationships[target_id].score - 5)
        if agent_id in target_agent.relationships:
            target_agent.relationships[agent_id].score = max(0, target_agent.relationships[agent_id].score - 15)
        
        # 添加记忆
        if contraband_found:
            message = f"检查{target_agent.name}时发现违禁品: {', '.join(contraband_found)}"
            target_agent.memory["episodic"].append(f"被狱警{agent.name}检查，发现了违禁品")
        else:
            message = f"检查{target_agent.name}，未发现违禁品"
            target_agent.memory["episodic"].append(f"被狱警{agent.name}搜身检查")
        
        agent.memory["episodic"].append(message)
        
        # 记录事件
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="patrol_inspect",
            description=message,
            details=json.dumps({
                "target_id": target_id,
                "target_name": target_agent.name,
                "contraband_found": contraband_found,
                "action_points_remaining": agent.action_points
            })
        )
        
        world_state.event_log.append(f"🔍 {message}")
        return ActionResult(success=True, message="检查完成", world_state_changed=True)


class EnforcePunishmentAction(BaseAction):
    """狱警执行惩罚"""
    def __init__(self):
        super().__init__(ActionEnum.ENFORCE_PUNISHMENT, 2)
    
    def can_execute(self, world_state: WorldState, agent_id: str, **kwargs) -> bool:
        agent = world_state.agents.get(agent_id)
        return agent and agent.role.value == "Guard" and agent.action_points >= self.ap_cost
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        target_id = kwargs.get('target_id')
        punishment_type = kwargs.get('punishment_type', 'isolation')
        
        if not target_id or target_id not in world_state.agents:
            return ActionResult(success=False, message="需要指定惩罚目标")
        
        target_agent = world_state.agents[target_id]
        
        if target_agent.role.value != "Prisoner":
            return ActionResult(success=False, message="只能惩罚囚犯")
        
        # 检查距离
        distance = abs(agent.position[0] - target_agent.position[0]) + abs(agent.position[1] - target_agent.position[1])
        if distance > 2:
            return ActionResult(success=False, message="目标距离太远")
        
        agent.action_points -= self.ap_cost
        
        # 执行惩罚效果
        if punishment_type == 'isolation':
            target_agent.sanity = max(0, target_agent.sanity - 20)
            punishment_desc = "被关禁闭"
        elif punishment_type == 'labor':
            target_agent.strength = max(0, target_agent.strength - 15)
            punishment_desc = "被罚劳动"
        elif punishment_type == 'restriction':
            target_agent.action_points = max(0, target_agent.action_points - 1)
            punishment_desc = "被限制行动"
        else:
            punishment_desc = "受到纪律处分"
        
        # 影响关系 - 严重影响
        if agent_id in target_agent.relationships:
            target_agent.relationships[agent_id].score = max(0, target_agent.relationships[agent_id].score - 25)
            target_agent.relationships[agent_id].context = "施暴的狱警"
        
        if target_id in agent.relationships:
            agent.relationships[target_id].score = max(0, agent.relationships[target_id].score - 10)
            agent.relationships[target_id].context = "被惩罚的囚犯"
        
        # 添加记忆
        agent.memory["episodic"].append(f"对{target_agent.name}执行{punishment_desc}")
        target_agent.memory["episodic"].append(f"被狱警{agent.name}{punishment_desc}")
        
        # 记录事件
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="punishment",
            description=f"对{target_agent.name}执行{punishment_desc}",
            details=json.dumps({
                "target_id": target_id,
                "target_name": target_agent.name,
                "punishment_type": punishment_type,
                "punishment_desc": punishment_desc,
                "action_points_remaining": agent.action_points
            })
        )
        
        world_state.event_log.append(f"⚖️ 狱警{agent.name}对{target_agent.name}执行{punishment_desc}")
        return ActionResult(success=True, message="惩罚已执行", world_state_changed=True)


# ==================== PRISONER-SPECIFIC ACTIONS ====================

class StealItemAction(BaseAction):
    """囚犯偷取物品"""
    def __init__(self):
        super().__init__(ActionEnum.STEAL_ITEM, 2)
    
    def can_execute(self, world_state: WorldState, agent_id: str, **kwargs) -> bool:
        agent = world_state.agents.get(agent_id)
        return agent and agent.role.value == "Prisoner" and agent.action_points >= self.ap_cost
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        target_id = kwargs.get('target_id')
        
        if not target_id or target_id not in world_state.agents:
            return ActionResult(success=False, message="需要指定偷取目标")
        
        target_agent = world_state.agents[target_id]
        
        # 检查距离
        distance = abs(agent.position[0] - target_agent.position[0]) + abs(agent.position[1] - target_agent.position[1])
        if distance > 1:
            return ActionResult(success=False, message="目标距离太远")
        
        if not target_agent.inventory:
            return ActionResult(success=False, message="目标没有物品可偷")
        
        agent.action_points -= self.ap_cost
        
        # 偷取成功率基于敏捷度（用logic代替）
        success_rate = agent.traits.logic * 0.8 + random.random() * 0.4
        
        if success_rate > 0.5:  # 偷取成功
            stolen_item = random.choice(target_agent.inventory)
            target_agent.inventory.remove(stolen_item)
            agent.inventory.append(stolen_item)
            
            # 影响关系
            if agent_id in target_agent.relationships:
                target_agent.relationships[agent_id].score = max(0, target_agent.relationships[agent_id].score - 30)
                target_agent.relationships[agent_id].context = "偷我东西的小偷"
            
            # 有概率被发现
            if random.random() < 0.3:  # 30%概率被发现
                agent.memory["episodic"].append(f"偷取了{target_agent.name}的{stolen_item.name}但被发现了")
                target_agent.memory["episodic"].append(f"发现{agent.name}偷了我的{stolen_item.name}")
                message = f"偷取{target_agent.name}的{stolen_item.name}但被发现"
            else:
                agent.memory["episodic"].append(f"成功偷取了{target_agent.name}的{stolen_item.name}")
                message = f"成功偷取{target_agent.name}的{stolen_item.name}"
        else:  # 偷取失败
            agent.memory["episodic"].append(f"试图偷取{target_agent.name}的物品但失败了")
            target_agent.memory["episodic"].append(f"发现{agent.name}试图偷我的东西")
            
            # 失败时严重影响关系
            if agent_id in target_agent.relationships:
                target_agent.relationships[agent_id].score = max(0, target_agent.relationships[agent_id].score - 40)
            
            message = f"偷取{target_agent.name}的物品失败"
        
        # 记录事件
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="theft",
            description=message,
            details=json.dumps({
                "target_id": target_id,
                "target_name": target_agent.name,
                "success": success_rate > 0.5,
                "item_stolen": stolen_item.name if success_rate > 0.5 else None,
                "action_points_remaining": agent.action_points
            })
        )
        
        world_state.event_log.append(f"🕵️ {message}")
        return ActionResult(success=True, message="偷取尝试完成", world_state_changed=True)


class FormAllianceAction(BaseAction):
    """囚犯组织联盟"""
    def __init__(self):
        super().__init__(ActionEnum.FORM_ALLIANCE, 2)
    
    def can_execute(self, world_state: WorldState, agent_id: str, **kwargs) -> bool:
        agent = world_state.agents.get(agent_id)
        return agent and agent.role.value == "Prisoner" and agent.action_points >= self.ap_cost
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        target_id = kwargs.get('target_id')
        alliance_name = kwargs.get('alliance_name', '囚犯联盟')
        
        if not target_id or target_id not in world_state.agents:
            return ActionResult(success=False, message="需要指定联盟伙伴")
        
        target_agent = world_state.agents[target_id]
        
        if target_agent.role.value != "Prisoner":
            return ActionResult(success=False, message="只能与其他囚犯结盟")
        
        # 检查距离
        distance = abs(agent.position[0] - target_agent.position[0]) + abs(agent.position[1] - target_agent.position[1])
        if distance > 2:
            return ActionResult(success=False, message="目标距离太远")
        
        agent.action_points -= self.ap_cost
        
        # 建立联盟关系
        if agent_id in target_agent.relationships:
            target_agent.relationships[agent_id].score = min(100, target_agent.relationships[agent_id].score + 30)
            target_agent.relationships[agent_id].context = f"{alliance_name}成员"
        
        if target_id in agent.relationships:
            agent.relationships[target_id].score = min(100, agent.relationships[target_id].score + 30)
            agent.relationships[target_id].context = f"{alliance_name}成员"
        
        # 添加记忆
        agent.memory["episodic"].append(f"与{target_agent.name}组建了{alliance_name}")
        target_agent.memory["episodic"].append(f"与{agent.name}组建了{alliance_name}")
        
        # 记录事件
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="alliance",
            description=f"与{target_agent.name}组建{alliance_name}",
            details=json.dumps({
                "target_id": target_id,
                "target_name": target_agent.name,
                "alliance_name": alliance_name,
                "action_points_remaining": agent.action_points
            })
        )
        
        world_state.event_log.append(f"🤝 {agent.name}与{target_agent.name}组建了{alliance_name}")
        return ActionResult(success=True, message="联盟已建立", world_state_changed=True)


class CraftWeaponAction(BaseAction):
    """囚犯制作武器"""
    def __init__(self):
        super().__init__(ActionEnum.CRAFT_WEAPON, 3)
    
    def can_execute(self, world_state: WorldState, agent_id: str, **kwargs) -> bool:
        agent = world_state.agents.get(agent_id)
        if not agent or agent.role.value != "Prisoner" or agent.action_points < self.ap_cost:
            return False
        
        # 需要材料
        required_materials = ["spoon", "bedsheet", "soap"]
        available_materials = [item.item_type.value for item in agent.inventory]
        
        return any(material in available_materials for material in required_materials)
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        
        # 查找可用材料
        available_items = []
        for item in agent.inventory:
            if item.item_type.value in ["spoon", "bedsheet", "soap"]:
                available_items.append(item)
        
        if not available_items:
            return ActionResult(success=False, message="没有制作材料")
        
        agent.action_points -= self.ap_cost
        
        # 消耗材料制作武器
        material_used = available_items[0]
        agent.inventory.remove(material_used)
        
        # 制作成功率基于logic和resilience
        success_rate = (agent.traits.logic + agent.traits.resilience) * 0.6 + random.random() * 0.4
        
        from models.schemas import Item
        
        if success_rate > 0.6:  # 制作成功
            shiv = Item(
                item_id=f"shiv_{agent_id}_{world_state.hour}",
                name="简易刀具",
                description="用监狱材料制作的简易武器",
                item_type=ItemEnum.SHIV
            )
            agent.inventory.append(shiv)
            
            agent.memory["episodic"].append(f"用{material_used.name}制作了简易刀具")
            message = f"成功制作了简易刀具"
        else:  # 制作失败
            agent.memory["episodic"].append(f"尝试用{material_used.name}制作武器但失败了")
            message = f"制作武器失败，浪费了{material_used.name}"
        
        # 记录事件
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="crafting",
            description=message,
            details=json.dumps({
                "material_used": material_used.name,
                "success": success_rate > 0.6,
                "weapon_created": "shiv" if success_rate > 0.6 else None,
                "action_points_remaining": agent.action_points
            })
        )
        
        world_state.event_log.append(f"🔨 {agent.name} {message}")
        return ActionResult(success=True, message="制作尝试完成", world_state_changed=True)


class SpreadRumorAction(BaseAction):
    """囚犯散布谣言"""
    def __init__(self):
        super().__init__(ActionEnum.SPREAD_RUMOR, 1)
    
    def can_execute(self, world_state: WorldState, agent_id: str, **kwargs) -> bool:
        agent = world_state.agents.get(agent_id)
        return agent and agent.role.value == "Prisoner" and agent.action_points >= self.ap_cost
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        rumor_text = kwargs.get('rumor_text', '监狱即将发生变化')
        
        agent.action_points -= self.ap_cost
        
        # 影响范围内的囚犯
        affected_prisoners = []
        for other_id, other_agent in world_state.agents.items():
            if other_agent.role.value == "Prisoner" and other_id != agent_id:
                distance = abs(agent.position[0] - other_agent.position[0]) + abs(agent.position[1] - other_agent.position[1])
                if distance <= 5:  # 谣言传播范围
                    other_agent.memory["episodic"].append(f"听到{agent.name}说: {rumor_text}")
                    
                    # 谣言可能影响关系或状态
                    if "狱警" in rumor_text:
                        other_agent.sanity = max(0, other_agent.sanity - 5)  # 负面谣言影响心理
                    elif "逃跑" in rumor_text:
                        other_agent.sanity = min(100, other_agent.sanity + 5)  # 希望谣言提升心理
                    
                    affected_prisoners.append(other_agent.name)
        
        agent.memory["episodic"].append(f"散布谣言: {rumor_text}")
        
        # 记录事件
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="rumor",
            description=f"散布谣言: {rumor_text}",
            details=json.dumps({
                "rumor_text": rumor_text,
                "affected_prisoners": affected_prisoners,
                "action_points_remaining": agent.action_points
            })
        )
        
        world_state.event_log.append(f"📢 {agent.name}散布谣言: {rumor_text}")
        return ActionResult(success=True, message="谣言已散布", world_state_changed=True)


class AssignTaskAction(BaseAction):
    """狱警分配任务"""
    def __init__(self):
        super().__init__(ActionEnum.ASSIGN_TASK, 1)
    
    def can_execute(self, world_state: WorldState, agent_id: str, **kwargs) -> bool:
        agent = world_state.agents.get(agent_id)
        return agent and agent.role.value == "Guard" and agent.action_points >= self.ap_cost
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        target_id = kwargs.get('target_id')
        task_text = kwargs.get('task_text', "清洁区域")
        
        if not target_id or target_id not in world_state.agents:
            return ActionResult(success=False, message="需要指定任务目标")
        
        target_agent = world_state.agents[target_id]
        if target_agent.role.value != "Prisoner":
            return ActionResult(success=False, message="只能给囚犯分配任务")
        
        agent.action_points -= self.ap_cost
        
        # 任务分配影响关系和状态
        if agent_id in target_agent.relationships:
            # 接受任务的囚犯对狱警关系轻微下降（被强制）
            target_agent.relationships[agent_id].score = max(0, target_agent.relationships[agent_id].score - 3)
            target_agent.relationships[agent_id].context = "任务分配者"
        
        if target_id in agent.relationships:
            # 狱警对囚犯的监管关系略微增强
            agent.relationships[target_id].score = min(100, agent.relationships[target_id].score + 2)
        
        # 被分配任务的囚犯会感到压力
        target_agent.sanity = max(0, target_agent.sanity - 5)
        
        # 添加记忆
        agent.memory["episodic"].append(f"给{target_agent.name}分配任务: {task_text}")
        target_agent.memory["episodic"].append(f"被狱警{agent.name}分配任务: {task_text}")
        
        # 记录事件
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="task_assignment",
            description=f"给{target_agent.name}分配任务: {task_text}",
            details=json.dumps({
                "target_id": target_id,
                "target_name": target_agent.name,
                "task_text": task_text,
                "action_points_remaining": agent.action_points
            })
        )
        
        world_state.event_log.append(f"📝 狱警{agent.name}给{target_agent.name}分配任务: {task_text}")
        return ActionResult(success=True, message="任务已分配", world_state_changed=True)


class EmergencyAssemblyAction(BaseAction):
    """狱警紧急集合"""
    def __init__(self):
        super().__init__(ActionEnum.EMERGENCY_ASSEMBLY, 3)  # 高消耗行动力
    
    def can_execute(self, world_state: WorldState, agent_id: str, **kwargs) -> bool:
        agent = world_state.agents.get(agent_id)
        return agent and agent.role.value == "Guard" and agent.action_points >= self.ap_cost
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        assembly_reason = kwargs.get('reason', "紧急情况")
        
        agent.action_points -= self.ap_cost
        
        # 影响所有囚犯
        affected_prisoners = []
        for other_id, other_agent in world_state.agents.items():
            if other_agent.role.value == "Prisoner":
                # 紧急集合造成恐慌和服从
                other_agent.sanity = max(0, other_agent.sanity - 15)
                other_agent.strength = max(0, other_agent.strength - 5)  # 紧张导致体力下降
                
                # 关系影响
                if agent_id in other_agent.relationships:
                    other_agent.relationships[agent_id].score = max(0, other_agent.relationships[agent_id].score - 8)
                    other_agent.relationships[agent_id].context = "紧急权威"
                
                # 添加记忆
                other_agent.memory["episodic"].append(f"狱警{agent.name}发起紧急集合: {assembly_reason}")
                affected_prisoners.append(other_agent.name)
        
        # 狱警记忆
        agent.memory["episodic"].append(f"发起紧急集合: {assembly_reason}")
        
        # 记录事件
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="emergency_assembly",
            description=f"发起紧急集合: {assembly_reason}",
            details=json.dumps({
                "reason": assembly_reason,
                "affected_prisoners": affected_prisoners,
                "action_points_remaining": agent.action_points
            })
        )
        
        world_state.event_log.append(f"🚨 狱警{agent.name}发起紧急集合: {assembly_reason}")
        return ActionResult(success=True, message="紧急集合已发起", world_state_changed=True)


class DigTunnelAction(BaseAction):
    """囚犯挖掘地道"""
    def __init__(self):
        super().__init__(ActionEnum.DIG_TUNNEL, 3)  # 高消耗行动力
    
    def can_execute(self, world_state: WorldState, agent_id: str, **kwargs) -> bool:
        agent = world_state.agents.get(agent_id)
        if not agent or agent.role.value != "Prisoner" or agent.action_points < self.ap_cost:
            return False
        
        # 需要有挖掘工具
        has_tool = False
        for item in agent.inventory:
            if item.item_type.value in ["spoon", "toolbox"]:
                has_tool = True
                break
        
        return has_tool
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        location = kwargs.get('location', "牢房角落")
        
        agent.action_points -= self.ap_cost
        
        # 挖掘成功率基于逻辑和体力
        success_rate = (agent.personality_traits.logic + agent.strength) / 200.0
        success_rate = min(0.7, max(0.1, success_rate))  # 限制在10%-70%之间
        
        is_successful = random.random() < success_rate
        
        # 挖掘消耗大量体力和精神
        agent.strength = max(0, agent.strength - 20)
        agent.sanity = max(0, agent.sanity - 10)
        agent.hunger = min(100, agent.hunger + 15)  # 体力劳动增加饥饿
        
        if is_successful:
            # 成功挖掘，增加逃跑希望
            agent.sanity = min(100, agent.sanity + 25)  # 希望提升精神
            message = f"在{location}成功挖掘了一段地道"
            event_type = "tunnel_success"
            
            # 可能被其他囚犯发现
            discovered_by = []
            for other_id, other_agent in world_state.agents.items():
                if other_agent.role.value == "Prisoner" and other_id != agent_id:
                    distance = abs(agent.position[0] - other_agent.position[0]) + abs(agent.position[1] - other_agent.position[1])
                    if distance <= 3 and random.random() < 0.3:  # 30%概率被发现
                        other_agent.memory["episodic"].append(f"发现{agent.name}在挖掘地道")
                        discovered_by.append(other_agent.name)
        else:
            message = f"在{location}挖掘地道失败"
            event_type = "tunnel_failure"
            discovered_by = []
        
        # 添加记忆
        agent.memory["episodic"].append(message)
        
        # 记录事件
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type=event_type,
            description=message,
            details=json.dumps({
                "location": location,
                "success_rate": success_rate,
                "successful": is_successful,
                "discovered_by": discovered_by,
                "action_points_remaining": agent.action_points
            })
        )
        
        if is_successful:
            world_state.event_log.append(f"🕳️ {agent.name}在{location}成功挖掘地道")
        else:
            world_state.event_log.append(f"❌ {agent.name}在{location}挖掘地道失败")
        
        return ActionResult(success=True, message=message, world_state_changed=True)


# Action registry
ACTION_REGISTRY = {
    # Basic Actions
    ActionEnum.DO_NOTHING: DoNothingAction,
    ActionEnum.MOVE: MoveAction,
    ActionEnum.SPEAK: SpeakAction,
    ActionEnum.ATTACK: AttackAction,
    ActionEnum.USE_ITEM: UseItemAction,
    ActionEnum.GIVE_ITEM: GiveItemAction,
    
    # Guard-specific Actions (5 new behaviors)
    ActionEnum.ANNOUNCE_RULE: AnnounceRuleAction,
    ActionEnum.PATROL_INSPECT: PatrolInspectAction,
    ActionEnum.ENFORCE_PUNISHMENT: EnforcePunishmentAction,
    ActionEnum.ASSIGN_TASK: AssignTaskAction,
    ActionEnum.EMERGENCY_ASSEMBLY: EmergencyAssemblyAction,
    
    # Prisoner-specific Actions (5 new behaviors)
    ActionEnum.STEAL_ITEM: StealItemAction,
    ActionEnum.FORM_ALLIANCE: FormAllianceAction,
    ActionEnum.CRAFT_WEAPON: CraftWeaponAction,
    ActionEnum.SPREAD_RUMOR: SpreadRumorAction,
    ActionEnum.DIG_TUNNEL: DigTunnelAction,
}