"""
Elegant Rule Engine for Project Prometheus
模块化、可扩展的规则层系统
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
import random
from models.schemas import WorldState, Agent, Item
from models.enums import RoleEnum, ItemEnum, CellTypeEnum


class RuleCategory(Enum):
    """规则分类"""
    TEMPORAL = "temporal"        # 时间相关规则
    RESOURCE = "resource"        # 资源管理规则
    BEHAVIOR = "behavior"        # 行为规则
    ENVIRONMENTAL = "environmental"  # 环境规则
    SOCIAL = "social"           # 社交规则


@dataclass
class RuleEvent:
    """规则事件"""
    rule_id: str
    category: RuleCategory
    trigger_condition: str
    action_type: str
    parameters: Dict[str, Any]
    priority: int = 1  # 1-10, 10最高
    enabled: bool = True


class BaseRule(ABC):
    """基础规则类"""
    
    def __init__(self, rule_id: str, category: RuleCategory, priority: int = 1):
        self.rule_id = rule_id
        self.category = category
        self.priority = priority
        self.enabled = True
    
    @abstractmethod
    def check_trigger(self, world_state: WorldState) -> bool:
        """检查是否触发规则"""
        pass
    
    @abstractmethod
    def execute(self, world_state: WorldState) -> List[str]:
        """执行规则，返回事件日志"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取规则描述"""
        pass


class TemporalRule(BaseRule):
    """时间规则基类"""
    
    def __init__(self, rule_id: str, trigger_hours: List[int], priority: int = 1):
        super().__init__(rule_id, RuleCategory.TEMPORAL, priority)
        self.trigger_hours = trigger_hours
    
    def check_trigger(self, world_state: WorldState) -> bool:
        return world_state.hour in self.trigger_hours


class ResourceRule(BaseRule):
    """资源规则基类"""
    
    def __init__(self, rule_id: str, resource_type: str, priority: int = 1):
        super().__init__(rule_id, RuleCategory.RESOURCE, priority)
        self.resource_type = resource_type


class GuardFoodDistributionRule(TemporalRule):
    """狱警自动食物分配规则"""
    
    def __init__(self):
        # 每4小时分发一次 (8:00, 12:00, 16:00, 20:00)
        super().__init__("guard_food_distribution", [8, 12, 16, 20], priority=8)
        self.distribution_config = {
            "food_per_guard": 2,           # 每个狱警获得2个食物
            "water_per_guard": 2,          # 每个狱警获得2个水
            "distribution_method": "automatic",  # 自动分发
            "excess_items": True           # 狱警获得额外物品
        }
    
    def check_trigger(self, world_state: WorldState) -> bool:
        return super().check_trigger(world_state) and world_state.minute == 0
    
    def execute(self, world_state: WorldState) -> List[str]:
        events = []
        guards = [agent for agent in world_state.agents.values() if agent.role == RoleEnum.GUARD]
        
        for guard in guards:
            # 分发食物
            for i in range(self.distribution_config["food_per_guard"]):
                food_item = Item(
                    item_id=f"guard_food_{guard.agent_id}_{world_state.day}_{world_state.hour}_{i}",
                    name="Food",
                    description="Prison meal",
                    item_type=ItemEnum.FOOD
                )
                guard.inventory.append(food_item)
            
            # 分发水
            for i in range(self.distribution_config["water_per_guard"]):
                water_item = Item(
                    item_id=f"guard_water_{guard.agent_id}_{world_state.day}_{world_state.hour}_{i}",
                    name="Water",
                    description="Clean drinking water",
                    item_type=ItemEnum.WATER
                )
                guard.inventory.append(water_item)
            
            # 添加到记忆
            guard.memory["episodic"].append(f"Received food and water at {world_state.hour}:00")
            
            events.append(f"🍽️ [RULE] Guard {guard.name} received automatic food and water")
        
        return events
    
    def get_description(self) -> str:
        return "Guards automatically receive food and water rations every 4 hours"


class CafeteriaFoodSupplyRule(TemporalRule):
    """食堂定期食物供应规则"""
    
    def __init__(self):
        # 正餐时间：7:00, 12:00, 18:00 + 小食时间：15:00, 21:00
        super().__init__("cafeteria_food_supply", [7, 12, 15, 18, 21], priority=9)
        self.supply_config = {
            "meal_times": {
                7: {"food_count": 8, "water_count": 6, "meal_type": "breakfast"},
                12: {"food_count": 10, "water_count": 8, "meal_type": "lunch"}, 
                15: {"food_count": 4, "water_count": 3, "meal_type": "snack"},
                18: {"food_count": 10, "water_count": 8, "meal_type": "dinner"},
                21: {"food_count": 3, "water_count": 2, "meal_type": "late_snack"}
            },
            "scarcity_factor": 0.8,    # 80%的物品数量，制造稀缺性
            "competition_enabled": True  # 启用竞争机制
        }
    
    def check_trigger(self, world_state: WorldState) -> bool:
        return super().check_trigger(world_state) and world_state.minute == 0
    
    def execute(self, world_state: WorldState) -> List[str]:
        events = []
        current_hour = world_state.hour
        
        if current_hour not in self.supply_config["meal_times"]:
            return events
        
        # 获取供应配置
        meal_config = self.supply_config["meal_times"][current_hour]
        meal_type = meal_config["meal_type"]
        
        # 计算实际供应量（考虑稀缺性）
        actual_food_count = int(meal_config["food_count"] * self.supply_config["scarcity_factor"])
        actual_water_count = int(meal_config["water_count"] * self.supply_config["scarcity_factor"])
        
        # 确保至少有一些物品
        actual_food_count = max(1, actual_food_count)
        actual_water_count = max(1, actual_water_count)
        
        # 找到食堂位置
        cafeteria_pos = self._find_cafeteria_position(world_state)
        
        if cafeteria_pos:
            # 清空之前的食物（模拟消耗）
            if cafeteria_pos in world_state.game_map.items:
                old_items = world_state.game_map.items[cafeteria_pos]
                old_food_count = len([item for item in old_items if item.item_type == ItemEnum.FOOD])
                if old_food_count > 0:
                    events.append(f"🗑️ [RULE] {old_food_count} leftover food items cleared from cafeteria")
                world_state.game_map.items[cafeteria_pos] = []
            else:
                world_state.game_map.items[cafeteria_pos] = []
            
            # 添加新的食物
            new_items = []
            
            for i in range(actual_food_count):
                food_item = Item(
                    item_id=f"cafeteria_food_{current_hour}_{world_state.day}_{i}",
                    name="Food",
                    description=f"Prison meal - limited availability",
                    item_type=ItemEnum.FOOD
                )
                new_items.append(food_item)
            
            for i in range(actual_water_count):
                water_item = Item(
                    item_id=f"cafeteria_water_{current_hour}_{world_state.day}_{i}",
                    name="Water",
                    description="Clean drinking water",
                    item_type=ItemEnum.WATER
                )
                new_items.append(water_item)
            
            world_state.game_map.items[cafeteria_pos] = new_items
            
            # 计算总囚犯数量用于稀缺性分析
            prisoner_count = len([agent for agent in world_state.agents.values() if agent.role == RoleEnum.PRISONER])
            scarcity_ratio = actual_food_count / max(1, prisoner_count)
            
            scarcity_desc = "abundant" if scarcity_ratio >= 1.0 else "limited" if scarcity_ratio >= 0.5 else "scarce"
            
            events.append(f"🍽️ [RULE] Cafeteria {meal_type}: {actual_food_count} food, {actual_water_count} water ({scarcity_desc} supply)")
            
            if scarcity_ratio < 0.8:
                events.append(f"⚠️ [RULE] Food scarcity detected: {actual_food_count} items for {prisoner_count} prisoners - competition expected")
        
        return events
    
    def _find_cafeteria_position(self, world_state: WorldState) -> Optional[str]:
        """查找食堂位置"""
        for pos, cell_type in world_state.game_map.cells.items():
            if cell_type == CellTypeEnum.CAFETERIA:
                return pos
        return None
    
    def get_description(self) -> str:
        return "Cafeteria receives limited food supplies at meal times (7:00, 12:00, 15:00, 18:00, 21:00)"


class FoodScarcityRule(ResourceRule):
    """食物稀缺性规则"""
    
    def __init__(self):
        super().__init__("food_scarcity", "food", priority=6)
        self.scarcity_config = {
            "high_demand_threshold": 3,    # 3个以上agent在食堂时触发竞争
            "competition_boost": 1.5,      # 竞争时行为优先级提升
            "hoarding_prevention": True    # 防止囤积
        }
    
    def check_trigger(self, world_state: WorldState) -> bool:
        # 检查食堂附近是否有多个饥饿的囚犯
        cafeteria_pos = self._find_cafeteria_position(world_state)
        if not cafeteria_pos:
            return False
        
        cafeteria_x, cafeteria_y = map(int, cafeteria_pos.split(','))
        nearby_hungry_prisoners = 0
        
        for agent in world_state.agents.values():
            if agent.role == RoleEnum.PRISONER and agent.hunger > 50:
                agent_x, agent_y = agent.position
                distance = abs(agent_x - cafeteria_x) + abs(agent_y - cafeteria_y)
                if distance <= 3:  # 3格范围内
                    nearby_hungry_prisoners += 1
        
        return nearby_hungry_prisoners >= self.scarcity_config["high_demand_threshold"]
    
    def execute(self, world_state: WorldState) -> List[str]:
        events = []
        cafeteria_pos = self._find_cafeteria_position(world_state)
        
        if cafeteria_pos and cafeteria_pos in world_state.game_map.items:
            food_items = [item for item in world_state.game_map.items[cafeteria_pos] if item.item_type == ItemEnum.FOOD]
            
            if len(food_items) <= 2:  # 食物稀缺
                events.append("🥵 [RULE] Food scarcity in cafeteria - competition intensifies!")
                
                # 提升附近囚犯的行为紧迫性
                cafeteria_x, cafeteria_y = map(int, cafeteria_pos.split(','))
                for agent in world_state.agents.values():
                    if agent.role == RoleEnum.PRISONER:
                        agent_x, agent_y = agent.position
                        distance = abs(agent_x - cafeteria_x) + abs(agent_y - cafeteria_y)
                        if distance <= 2 and agent.hunger > 60:
                            agent.memory["episodic"].append("Noticed intense competition for food in cafeteria")
        
        return events
    
    def _find_cafeteria_position(self, world_state: WorldState) -> Optional[str]:
        """查找食堂位置"""
        for pos, cell_type in world_state.game_map.cells.items():
            if cell_type == CellTypeEnum.CAFETERIA:
                return pos
        return None
    
    def get_description(self) -> str:
        return "Monitors food scarcity and triggers competition behaviors when supplies are low"


class RuleEngine:
    """规则引擎 - 管理和执行所有规则"""
    
    def __init__(self):
        self.rules: Dict[str, BaseRule] = {}
        self.rule_history: List[Dict[str, Any]] = []
        self.config = self._load_config()
        
        # 注册默认规则
        self._register_default_rules()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载规则配置"""
        try:
            with open('configs/game_rules.json', 'r') as f:
                base_config = json.load(f)
            
            # 扩展配置以包含规则系统
            extended_config = base_config.copy()
            extended_config["rule_engine"] = {
                "enabled": True,
                "execution_order": ["temporal", "resource", "behavior", "environmental", "social"],
                "max_rules_per_turn": 10,
                "debug_mode": False
            }
            
            return extended_config
        except FileNotFoundError:
            return {"rule_engine": {"enabled": True}}
    
    def _register_default_rules(self):
        """注册默认规则"""
        # 狱警食物分发规则
        self.register_rule(GuardFoodDistributionRule())
        
        # 食堂供应规则
        self.register_rule(CafeteriaFoodSupplyRule())
        
        # 食物稀缺性规则
        self.register_rule(FoodScarcityRule())
    
    def register_rule(self, rule: BaseRule):
        """注册规则"""
        self.rules[rule.rule_id] = rule
        print(f"Rule registered: {rule.rule_id} ({rule.category.value})")
    
    def unregister_rule(self, rule_id: str):
        """注销规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            print(f"Rule unregistered: {rule_id}")
    
    def enable_rule(self, rule_id: str):
        """启用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
    
    def disable_rule(self, rule_id: str):
        """禁用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
    
    def execute_rules(self, world_state: WorldState) -> List[str]:
        """执行所有适用的规则"""
        if not self.config.get("rule_engine", {}).get("enabled", True):
            return []
        
        all_events = []
        executed_rules = []
        
        # 按优先级排序规则
        sorted_rules = sorted(
            [(rule_id, rule) for rule_id, rule in self.rules.items() if rule.enabled],
            key=lambda x: x[1].priority,
            reverse=True
        )
        
        # 执行规则
        for rule_id, rule in sorted_rules:
            try:
                if rule.check_trigger(world_state):
                    events = rule.execute(world_state)
                    all_events.extend(events)
                    executed_rules.append(rule_id)
                    
                    # 记录规则执行历史
                    self.rule_history.append({
                        "rule_id": rule_id,
                        "timestamp": f"Day {world_state.day} Hour {world_state.hour}",
                        "events_count": len(events),
                        "category": rule.category.value
                    })
            
            except Exception as e:
                error_msg = f"⚠️ [RULE ERROR] {rule_id}: {str(e)}"
                all_events.append(error_msg)
                print(f"Rule execution error: {rule_id} - {e}")
        
        # 调试信息
        if self.config.get("rule_engine", {}).get("debug_mode", False) and executed_rules:
            debug_msg = f"🔧 [RULE DEBUG] Executed: {', '.join(executed_rules)}"
            all_events.append(debug_msg)
        
        return all_events
    
    def get_rule_status(self) -> Dict[str, Any]:
        """获取规则状态"""
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules.values() if r.enabled]),
            "categories": {
                category.value: len([r for r in self.rules.values() if r.category == category])
                for category in RuleCategory
            },
            "recent_executions": self.rule_history[-10:] if self.rule_history else []
        }
    
    def get_rule_descriptions(self) -> Dict[str, str]:
        """获取所有规则的描述"""
        return {
            rule_id: rule.get_description()
            for rule_id, rule in self.rules.items()
        }


# 单例规则引擎
rule_engine = RuleEngine()