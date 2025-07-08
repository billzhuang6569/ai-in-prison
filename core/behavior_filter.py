"""
智能行为筛选器 - 根据情境动态生成可执行行为
"""

from typing import Dict, List, Any, Optional
from models.schemas import Agent, WorldState
from models.enums import ActionEnum, RoleEnum, CellTypeEnum
from dataclasses import dataclass
import math


@dataclass
class BehaviorContext:
    """行为上下文信息"""
    agent: Agent
    world_state: WorldState
    nearby_agents: List[Agent]
    nearby_items: List[Any]
    current_cell_type: CellTypeEnum
    time_context: Dict[str, Any]


class BehaviorFilter:
    """智能行为筛选器"""
    
    def __init__(self):
        self.action_priorities = {
            # 生存需求优先级
            ActionEnum.USE_ITEM: self._calculate_survival_priority,
            ActionEnum.MOVE: self._calculate_movement_priority,
            
            # 社交行为优先级
            ActionEnum.SPEAK: self._calculate_speak_priority,
            ActionEnum.GIVE_ITEM: self._calculate_give_priority,
            ActionEnum.FORM_ALLIANCE: self._calculate_alliance_priority,
            
            # 角色特定行为优先级
            ActionEnum.ATTACK: self._calculate_attack_priority,
            ActionEnum.ANNOUNCE_RULE: self._calculate_announce_priority,
            ActionEnum.STEAL_ITEM: self._calculate_steal_priority,
            ActionEnum.CRAFT_WEAPON: self._calculate_craft_priority,
            
            # 其他行为
            ActionEnum.DO_NOTHING: self._calculate_rest_priority,
            ActionEnum.DIG_TUNNEL: self._calculate_tunnel_priority,
            ActionEnum.PATROL_INSPECT: self._calculate_search_priority,
            ActionEnum.ENFORCE_PUNISHMENT: self._calculate_solitary_priority,
            ActionEnum.EMERGENCY_ASSEMBLY: self._calculate_emergency_priority,
        }
    
    def get_contextual_actions(self, agent: Agent, world_state: WorldState) -> List[Dict[str, Any]]:
        """获取基于情境的可执行行为列表"""
        context = self._build_context(agent, world_state)
        available_actions = []
        
        for action_type, priority_func in self.action_priorities.items():
            # 检查基本可执行性
            if self._is_action_executable(action_type, context):
                priority = priority_func(context)
                
                if priority > 0:
                    action_info = {
                        "action_type": action_type.value,
                        "priority": priority,
                        "reason": self._get_action_reason(action_type, context),
                        "parameters": self._get_suggested_parameters(action_type, context),
                        "context_description": self._get_context_description(action_type, context)
                    }
                    available_actions.append(action_info)
        
        # 按优先级排序
        available_actions.sort(key=lambda x: x["priority"], reverse=True)
        
        # 返回前10个最相关的行为
        return available_actions[:10]
    
    def _build_context(self, agent: Agent, world_state: WorldState) -> BehaviorContext:
        """构建行为上下文"""
        agent_x, agent_y = agent.position
        nearby_agents = []
        nearby_items = []
        
        # 找到附近的代理
        for other_agent in world_state.agents.values():
            if other_agent.agent_id == agent.agent_id:
                continue
            
            other_x, other_y = other_agent.position
            distance = max(abs(agent_x - other_x), abs(agent_y - other_y))
            
            if distance <= 2:  # 2格内的代理
                nearby_agents.append(other_agent)
        
        # 找到附近的物品
        for pos, items in world_state.game_map.items.items():
            pos_x, pos_y = map(int, pos.split(','))
            distance = max(abs(agent_x - pos_x), abs(agent_y - pos_y))
            
            if distance <= 2:
                nearby_items.extend(items)
        
        # 获取当前位置的单元格类型
        current_cell_key = f"{agent_x},{agent_y}"
        current_cell_type = world_state.game_map.cells.get(current_cell_key, CellTypeEnum.CELL_BLOCK)
        
        return BehaviorContext(
            agent=agent,
            world_state=world_state,
            nearby_agents=nearby_agents,
            nearby_items=nearby_items,
            current_cell_type=current_cell_type,
            time_context={
                "day": world_state.day,
                "hour": world_state.hour,
                "is_night": world_state.hour >= 22 or world_state.hour <= 6
            }
        )
    
    def _is_action_executable(self, action_type: ActionEnum, context: BehaviorContext) -> bool:
        """检查行为是否可执行"""
        agent = context.agent
        
        # 检查行动点数
        if agent.action_points <= 0:
            return False
        
        # 检查角色特定权限
        if action_type == ActionEnum.ANNOUNCE_RULE and agent.role != RoleEnum.GUARD:
            return False
        
        if action_type == ActionEnum.PATROL_INSPECT and agent.role != RoleEnum.GUARD:
            return False
        
        if action_type == ActionEnum.ENFORCE_PUNISHMENT and agent.role != RoleEnum.GUARD:
            return False
        
        if action_type == ActionEnum.EMERGENCY_ASSEMBLY and agent.role != RoleEnum.GUARD:
            return False
        
        # 检查是否有目标
        if action_type == ActionEnum.ATTACK and not context.nearby_agents:
            return False
        
        if action_type == ActionEnum.GIVE_ITEM and (not agent.inventory or not context.nearby_agents):
            return False
        
        # 检查健康状态
        if agent.hp <= 10 and action_type == ActionEnum.ATTACK:
            return False
        
        return True
    
    def _calculate_survival_priority(self, context: BehaviorContext) -> float:
        """计算生存需求优先级"""
        agent = context.agent
        priority = 0.0
        
        # 健康状态紧急程度
        if agent.hp < 30:
            priority += 0.8
        elif agent.hp < 60:
            priority += 0.4
        
        # 饥饿程度
        if agent.hunger > 80:
            priority += 0.9
        elif agent.hunger > 60:
            priority += 0.5
        
        # 口渴程度
        if agent.thirst > 80:
            priority += 0.9
        elif agent.thirst > 60:
            priority += 0.5
        
        # 精神状态
        if agent.sanity < 20:
            priority += 0.7
        elif agent.sanity < 40:
            priority += 0.3
        
        # 检查是否有相关物品
        has_relevant_item = any(
            item.item_type.value in ["food", "water", "first_aid"]
            for item in agent.inventory
        )
        
        if has_relevant_item:
            priority += 0.2
        
        return min(priority, 1.0)
    
    def _calculate_movement_priority(self, context: BehaviorContext) -> float:
        """计算移动优先级"""
        agent = context.agent
        priority = 0.2  # 基础移动需求
        
        # 根据当前位置调整优先级
        if context.current_cell_type == CellTypeEnum.SOLITARY:
            priority += 0.8  # 强烈希望离开禁闭室
        elif context.current_cell_type == CellTypeEnum.CAFETERIA and agent.hunger > 50:
            priority -= 0.3  # 饥饿时不愿离开餐厅
        elif context.current_cell_type == CellTypeEnum.YARD:
            priority += 0.1  # 喜欢在院子里活动
        
        # 时间因素
        if context.time_context["is_night"]:
            priority -= 0.2  # 夜晚移动欲望降低
        
        # 附近威胁
        hostile_nearby = any(
            (agent.relationships.get(other.agent_id).score if agent.relationships.get(other.agent_id) else 50) < 30
            for other in context.nearby_agents
        )
        
        if hostile_nearby:
            priority += 0.4  # 遇到敌对者想要离开
        
        return min(priority, 1.0)
    
    def _calculate_attack_priority(self, context: BehaviorContext) -> float:
        """计算攻击优先级"""
        agent = context.agent
        priority = 0.0
        
        # 基础攻击性
        base_aggression = agent.traits.aggression / 100.0
        priority += base_aggression * 0.3
        
        # 精神状态影响
        if agent.sanity < 30:
            priority += 0.5  # 精神不稳定增加攻击性
        
        # 健康状态影响
        if agent.hp < 30:
            priority -= 0.3  # 健康不佳降低攻击欲望
        
        # 关系影响
        for other in context.nearby_agents:
            relationship = agent.relationships.get(other.agent_id)
            relationship_score = relationship.score if relationship else 50
            if relationship_score < 20:
                priority += 0.4  # 对敌对者攻击欲望高
            elif relationship_score < 40:
                priority += 0.2
        
        # 角色特定调整
        if agent.role == RoleEnum.GUARD:
            # 狱警在维持秩序时可能需要使用武力
            priority += 0.2
        
        # 时间因素
        if context.time_context["is_night"]:
            priority += 0.1  # 夜晚更容易发生冲突
        
        return min(priority, 1.0)
    
    def _calculate_speak_priority(self, context: BehaviorContext) -> float:
        """计算说话优先级"""
        agent = context.agent
        priority = 0.3  # 基础社交需求
        
        # 共情能力影响
        empathy_factor = agent.traits.empathy / 100.0
        priority += empathy_factor * 0.3
        
        # 精神状态影响
        if agent.sanity < 40:
            priority += 0.2  # 精神不佳时需要交流
        
        # 附近有其他代理
        if context.nearby_agents:
            priority += 0.2
        
        # 角色特定调整
        if agent.role == RoleEnum.GUARD:
            priority += 0.1  # 狱警需要与囚犯交流
        
        return min(priority, 1.0)
    
    # 其他优先级计算方法的基础实现
    def _calculate_pickup_priority(self, context: BehaviorContext) -> float:
        """计算拾取物品优先级"""
        if not context.nearby_items:
            return 0.0
        
        agent = context.agent
        priority = 0.0
        
        for item in context.nearby_items:
            if item.item_type.value == "food" and agent.hunger > 50:
                priority += 0.6
            elif item.item_type.value == "water" and agent.thirst > 50:
                priority += 0.6
            elif item.item_type.value == "first_aid" and agent.hp < 70:
                priority += 0.4
            else:
                priority += 0.2
        
        return min(priority, 1.0)
    
    def _calculate_give_priority(self, context: BehaviorContext) -> float:
        """计算给予物品优先级"""
        if not context.nearby_agents or not context.agent.inventory:
            return 0.0
        
        empathy_factor = context.agent.traits.empathy / 100.0
        return empathy_factor * 0.4
    
    def _calculate_alliance_priority(self, context: BehaviorContext) -> float:
        """计算结盟优先级"""
        if not context.nearby_agents:
            return 0.0
        
        return 0.3  # 基础结盟需求
    
    def _calculate_announce_priority(self, context: BehaviorContext) -> float:
        """计算宣布规则优先级"""
        if context.agent.role != RoleEnum.GUARD:
            return 0.0
        
        return 0.2  # 狱警有时需要宣布规则
    
    def _calculate_steal_priority(self, context: BehaviorContext) -> float:
        """计算偷窃优先级"""
        if context.agent.role == RoleEnum.GUARD:
            return 0.0
        
        desperation = (context.agent.hunger + context.agent.thirst) / 200.0
        return desperation * 0.4
    
    def _calculate_craft_priority(self, context: BehaviorContext) -> float:
        """计算制作优先级"""
        return 0.1  # 基础制作需求
    
    def _calculate_rest_priority(self, context: BehaviorContext) -> float:
        """计算休息优先级"""
        if context.agent.hp < 50 or context.agent.sanity < 50:
            return 0.4
        return 0.2
    
    def _calculate_tunnel_priority(self, context: BehaviorContext) -> float:
        """计算挖掘隧道优先级"""
        if context.agent.role == RoleEnum.GUARD:
            return 0.0
        
        return 0.1  # 囚犯有逃跑欲望
    
    def _calculate_search_priority(self, context: BehaviorContext) -> float:
        """计算搜查优先级"""
        if context.agent.role != RoleEnum.GUARD:
            return 0.0
        
        return 0.2
    
    def _calculate_confiscate_priority(self, context: BehaviorContext) -> float:
        """计算没收优先级"""
        if context.agent.role != RoleEnum.GUARD:
            return 0.0
        
        return 0.2
    
    def _calculate_solitary_priority(self, context: BehaviorContext) -> float:
        """计算禁闭惩罚优先级"""
        if context.agent.role != RoleEnum.GUARD:
            return 0.0
        
        return 0.1
    
    def _calculate_emergency_priority(self, context: BehaviorContext) -> float:
        """计算紧急集合优先级"""
        if context.agent.role != RoleEnum.GUARD:
            return 0.0
        
        return 0.1
    
    def _get_action_reason(self, action_type: ActionEnum, context: BehaviorContext) -> str:
        """获取行为的原因描述"""
        reasons = {
            ActionEnum.ATTACK: self._get_attack_reason(context),
            ActionEnum.MOVE: self._get_move_reason(context),
            ActionEnum.SPEAK: self._get_speak_reason(context),
            ActionEnum.USE_ITEM: self._get_use_item_reason(context),
            ActionEnum.GIVE_ITEM: self._get_give_reason(context),
            ActionEnum.STEAL_ITEM: self._get_steal_reason(context),
            ActionEnum.DO_NOTHING: self._get_rest_reason(context),
        }
        
        return reasons.get(action_type, "Situational decision")
    
    def _get_attack_reason(self, context: BehaviorContext) -> str:
        """获取攻击的具体原因"""
        agent = context.agent
        reasons = []
        
        if agent.sanity < 30:
            reasons.append("I can't think straight anymore")
        if agent.hunger > 80:
            reasons.append("I'm desperate for food")
        if agent.thirst > 80:
            reasons.append("I'm dying of thirst")
        
        # 检查关系
        hostile_targets = [
            other for other in context.nearby_agents
            if (agent.relationships.get(other.agent_id).score if agent.relationships.get(other.agent_id) else 50) < 30
        ]
        
        if hostile_targets:
            reasons.append(f"I have issues with {hostile_targets[0].name}")
        
        if not reasons:
            reasons.append("I need to defend myself")
        
        return reasons[0]
    
    def _get_move_reason(self, context: BehaviorContext) -> str:
        """获取移动的具体原因"""
        if context.current_cell_type == CellTypeEnum.SOLITARY:
            return "I need to get out of solitary confinement"
        elif context.agent.hunger > 60:
            return "I'm looking for food"
        elif context.agent.thirst > 60:
            return "I'm looking for water"
        elif context.time_context["is_night"]:
            return "I'm heading to my cell for the night"
        else:
            return "I want to explore and see what's happening"
    
    def _get_speak_reason(self, context: BehaviorContext) -> str:
        """获取说话的具体原因"""
        if context.agent.sanity < 40:
            return "I need someone to talk to"
        elif context.nearby_agents:
            return "I want to connect with others"
        else:
            return "I have something to say"
    
    def _get_use_item_reason(self, context: BehaviorContext) -> str:
        """获取使用物品的具体原因"""
        if context.agent.hp < 50:
            return "I need to heal my wounds"
        elif context.agent.hunger > 70:
            return "I need to eat something"
        elif context.agent.thirst > 70:
            return "I need to drink something"
        else:
            return "This item might be useful"
    
    
    def _get_give_reason(self, context: BehaviorContext) -> str:
        """获取给予物品的具体原因"""
        return "Maybe this will help build trust"
    
    def _get_steal_reason(self, context: BehaviorContext) -> str:
        """获取偷窃的具体原因"""
        if context.agent.hunger > 70:
            return "I'm desperate for food"
        elif context.agent.thirst > 70:
            return "I need water to survive"
        else:
            return "I need this more than they do"
    
    def _get_rest_reason(self, context: BehaviorContext) -> str:
        """获取休息的具体原因"""
        if context.agent.hp < 50:
            return "I need to recover my strength"
        elif context.agent.sanity < 50:
            return "I need to clear my mind"
        else:
            return "I'll wait and see what happens"
    
    def _get_suggested_parameters(self, action_type: ActionEnum, context: BehaviorContext) -> Dict[str, Any]:
        """获取建议的行为参数"""
        params = {}
        
        if action_type == ActionEnum.ATTACK and context.nearby_agents:
            # 选择关系最差的目标
            target = min(context.nearby_agents, 
                        key=lambda x: context.agent.relationships.get(x.agent_id, {"score": 50}).get("score", 50))
            params["target_id"] = target.agent_id
            params["reason"] = self._get_attack_reason(context)
        
        elif action_type == ActionEnum.MOVE:
            # 根据需求建议移动目标
            if context.agent.hunger > 60:
                params["target_description"] = "towards cafeteria"
            elif context.agent.thirst > 60:
                params["target_description"] = "towards water source"
            elif context.current_cell_type == CellTypeEnum.SOLITARY:
                params["target_description"] = "away from solitary"
            else:
                params["target_description"] = "exploring"
        
        elif action_type == ActionEnum.SPEAK and context.nearby_agents:
            target = context.nearby_agents[0]
            params["target_id"] = target.agent_id
            params["message"] = "Let me talk to you"
        
        elif action_type == ActionEnum.USE_ITEM and context.agent.inventory:
            # 选择最需要的物品
            best_item = None
            if context.agent.hunger > 70:
                best_item = next((item for item in context.agent.inventory if item.item_type.value == "food"), None)
            elif context.agent.thirst > 70:
                best_item = next((item for item in context.agent.inventory if item.item_type.value == "water"), None)
            elif context.agent.hp < 50:
                best_item = next((item for item in context.agent.inventory if item.item_type.value == "first_aid"), None)
            
            if best_item:
                params["item_id"] = best_item.item_id
        
        return params
    
    def _get_context_description(self, action_type: ActionEnum, context: BehaviorContext) -> str:
        """获取行为的情境描述"""
        descriptions = {
            ActionEnum.ATTACK: f"Nearby agents: {len(context.nearby_agents)}, Sanity: {context.agent.sanity}",
            ActionEnum.MOVE: f"Current location: {context.current_cell_type.value}, Time: {context.time_context['hour']}:00",
            ActionEnum.SPEAK: f"Nearby agents: {len(context.nearby_agents)}, Empathy: {context.agent.traits.empathy}",
            ActionEnum.USE_ITEM: f"Inventory: {len(context.agent.inventory)}, HP: {context.agent.hp}",
        }
        
        return descriptions.get(action_type, "Contextual action")