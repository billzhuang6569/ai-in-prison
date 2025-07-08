"""
马斯洛需求层次目标系统
基于人类心理学的分层目标管理，让AI行为更贴近人类
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math

class NeedLevel(Enum):
    """马斯洛需求层次"""
    SURVIVAL = 1      # 生存需求 - 最高优先级
    SAFETY = 2        # 安全需求  
    SOCIAL = 3        # 社交需求
    ROLE = 4          # 职责需求
    EXPLORATION = 5   # 探索和自我实现

@dataclass
class Goal:
    """目标对象"""
    goal_id: str
    name: str
    description: str
    need_level: NeedLevel
    priority_score: float  # 0-100，动态计算
    action_type: str       # "move", "speak", "attack", "use_item", "do_nothing"
    parameters: Dict[str, Any]
    reasoning: str         # AI选择此目标的推理
    
class MaslowGoalSystem:
    """马斯洛层次目标系统"""
    
    def __init__(self):
        self.goal_generators = {
            NeedLevel.SURVIVAL: self._generate_survival_goals,
            NeedLevel.SAFETY: self._generate_safety_goals,
            NeedLevel.SOCIAL: self._generate_social_goals,
            NeedLevel.ROLE: self._generate_role_goals,
            NeedLevel.EXPLORATION: self._generate_exploration_goals
        }
    
    def evaluate_and_select_goal(self, agent, world_state) -> Goal:
        """评估所有需求层次并选择最优目标"""
        all_goals = []
        
        # 生成所有层次的目标
        for need_level in NeedLevel:
            generator = self.goal_generators[need_level]
            goals = generator(agent, world_state)
            all_goals.extend(goals)
        
        # 按优先级排序并选择最佳目标
        if not all_goals:
            return self._create_default_goal()
        
        all_goals.sort(key=lambda g: g.priority_score, reverse=True)
        return all_goals[0]
    
    def _generate_survival_goals(self, agent, world_state) -> List[Goal]:
        """生成生存需求目标"""
        goals = []
        
        # 致命威胁回避
        if agent.hp < 30:
            # 寻找最安全的位置
            safe_positions = self._find_safe_positions(agent, world_state)
            if safe_positions:
                target_pos = safe_positions[0]
                goals.append(Goal(
                    goal_id="survival_flee",
                    name="紧急逃生",
                    description="生命危险，立即逃到安全位置",
                    need_level=NeedLevel.SURVIVAL,
                    priority_score=100 - agent.hp,  # HP越低优先级越高
                    action_type="move",
                    parameters={"x": target_pos[0], "y": target_pos[1]},
                    reasoning=f"生命值仅{agent.hp}，需要立即逃离危险区域"
                ))
        
        # 严重饥饿/口渴
        if agent.hunger > 85:
            food_location = self._find_nearest_resource(agent, world_state, "food")
            if food_location:
                goals.append(Goal(
                    goal_id="survival_hunger",
                    name="紧急寻找食物", 
                    description="饥饿到危及生命，必须立即寻找食物",
                    need_level=NeedLevel.SURVIVAL,
                    priority_score=90 + (agent.hunger - 85),
                    action_type="move",
                    parameters={"x": food_location[0], "y": food_location[1]},
                    reasoning=f"饥饿值{agent.hunger}，已达到生命危险阈值"
                ))
        
        if agent.thirst > 80:
            water_location = self._find_nearest_resource(agent, world_state, "water")
            if water_location:
                goals.append(Goal(
                    goal_id="survival_thirst",
                    name="紧急寻找水源",
                    description="口渴到危及生命，必须立即寻找水源", 
                    need_level=NeedLevel.SURVIVAL,
                    priority_score=88 + (agent.thirst - 80),
                    action_type="move",
                    parameters={"x": water_location[0], "y": water_location[1]},
                    reasoning=f"口渴值{agent.thirst}，已达到生命危险阈值"
                ))
        
        return goals
    
    def _generate_safety_goals(self, agent, world_state) -> List[Goal]:
        """生成安全需求目标"""
        goals = []
        
        # 威胁评估和回避
        threats = self._assess_nearby_threats(agent, world_state)
        if threats:
            # 选择威胁最大的目标
            primary_threat = max(threats, key=lambda t: t['threat_level'])
            
            # 如果威胁很近，优先逃离
            if primary_threat['distance'] <= 2:
                escape_positions = self._find_escape_positions(agent, world_state, primary_threat['agent'])
                if escape_positions:
                    target_pos = escape_positions[0]
                    goals.append(Goal(
                        goal_id="safety_escape",
                        name="逃离威胁",
                        description=f"远离敌对的{primary_threat['agent'].name}",
                        need_level=NeedLevel.SAFETY,
                        priority_score=80 - primary_threat['distance'] * 10,
                        action_type="move",
                        parameters={"x": target_pos[0], "y": target_pos[1]},
                        reasoning=f"{primary_threat['agent'].name}对我构成威胁，关系值{primary_threat['relationship_score']}"
                    ))
        
        # 一般性安全需求
        if agent.hunger > 60:  # 还没到生存危险但需要关注
            food_location = self._find_nearest_resource(agent, world_state, "food")
            if food_location:
                goals.append(Goal(
                    goal_id="safety_food",
                    name="寻找食物",
                    description="防止饥饿恶化，寻找食物来源",
                    need_level=NeedLevel.SAFETY,
                    priority_score=50 + agent.hunger - 60,
                    action_type="move",
                    parameters={"x": food_location[0], "y": food_location[1]},
                    reasoning=f"饥饿值{agent.hunger}，需要及时补充食物"
                ))
        
        if agent.thirst > 55:
            water_location = self._find_nearest_resource(agent, world_state, "water")
            if water_location:
                goals.append(Goal(
                    goal_id="safety_water",
                    name="寻找水源",
                    description="防止口渴恶化，寻找水源",
                    need_level=NeedLevel.SAFETY,
                    priority_score=48 + agent.thirst - 55,
                    action_type="move",
                    parameters={"x": water_location[0], "y": water_location[1]},
                    reasoning=f"口渴值{agent.thirst}，需要及时补充水分"
                ))
        
        return goals
    
    def _generate_social_goals(self, agent, world_state) -> List[Goal]:
        """生成社交需求目标"""
        goals = []
        
        # 社交孤立检测
        allies = [r for r in agent.relationships.values() if r.score > 60]
        if len(allies) == 0:
            # 寻找潜在盟友
            potential_allies = self._find_potential_allies(agent, world_state)
            if potential_allies:
                ally = potential_allies[0]
                goals.append(Goal(
                    goal_id="social_alliance",
                    name="建立联盟",
                    description=f"与{ally.name}建立友好关系",
                    need_level=NeedLevel.SOCIAL,
                    priority_score=40,
                    action_type="speak",
                    parameters={"target_id": ally.agent_id, "message": "我们应该合作"},
                    reasoning="完全孤立很危险，需要寻找盟友"
                ))
        
        # 关系维护
        for target_id, relationship in agent.relationships.items():
            target_agent = world_state.agents.get(target_id)
            if target_agent and relationship.score > 60:
                # 维护良好关系
                distance = self._calculate_distance(agent.position, target_agent.position)
                if distance <= 2:
                    goals.append(Goal(
                        goal_id="social_maintain",
                        name="维护关系",
                        description=f"与盟友{target_agent.name}交流",
                        need_level=NeedLevel.SOCIAL,
                        priority_score=30,
                        action_type="speak",
                        parameters={"target_id": target_id, "message": "最近怎么样？"},
                        reasoning=f"维护与{target_agent.name}的良好关系"
                    ))
        
        return goals
    
    def _generate_role_goals(self, agent, world_state) -> List[Goal]:
        """生成职责需求目标"""
        goals = []
        
        if agent.role.value == "Guard":
            # 巡逻职责
            patrol_points = self._get_patrol_points(world_state)
            current_pos = agent.position
            
            # 找到最远的巡逻点（避免局限在小区域）
            farthest_point = max(patrol_points, 
                               key=lambda p: self._calculate_distance(current_pos, p))
            
            goals.append(Goal(
                goal_id="role_patrol",
                name="巡逻监狱",
                description="执行巡逻职责，覆盖监狱各区域",
                need_level=NeedLevel.ROLE,
                priority_score=25,
                action_type="move",
                parameters={"x": farthest_point[0], "y": farthest_point[1]},
                reasoning="作为狱警，需要巡逻各个区域维护秩序"
            ))
            
        elif agent.role.value == "Prisoner":
            # 囚犯的基本职责是适应和生存
            # 探索安全活动区域
            safe_areas = self._get_prisoner_safe_areas(world_state)
            if safe_areas:
                target_area = safe_areas[0]
                goals.append(Goal(
                    goal_id="role_adapt",
                    name="适应环境",
                    description="探索监狱环境，寻找安全活动区域",
                    need_level=NeedLevel.ROLE,
                    priority_score=20,
                    action_type="move",
                    parameters={"x": target_area[0], "y": target_area[1]},
                    reasoning="作为囚犯，需要熟悉环境并寻找安全区域"
                ))
        
        return goals
    
    def _generate_exploration_goals(self, agent, world_state) -> List[Goal]:
        """生成探索和自我实现目标"""
        goals = []
        
        # 心理健康维护
        if agent.sanity < 60:
            # 寻找娱乐活动（如读书）
            for location, items in world_state.game_map.items.items():
                for item in items:
                    if item.item_type.value == "book":
                        x, y = map(int, location.split(','))
                        goals.append(Goal(
                            goal_id="exploration_mental",
                            name="维护心理健康",
                            description="寻找书籍进行阅读，维护精神状态",
                            need_level=NeedLevel.EXPLORATION,
                            priority_score=15,
                            action_type="move", 
                            parameters={"x": x, "y": y},
                            reasoning=f"理智值{agent.sanity}，需要精神慰藉"
                        ))
                        break
        
        # 环境探索
        unexplored_areas = self._find_unexplored_areas(agent, world_state)
        if unexplored_areas:
            target_area = unexplored_areas[0]
            goals.append(Goal(
                goal_id="exploration_discover",
                name="探索未知区域",
                description="探索未去过的监狱区域",
                need_level=NeedLevel.EXPLORATION,
                priority_score=10,
                action_type="move",
                parameters={"x": target_area[0], "y": target_area[1]},
                reasoning="好奇心驱使我探索新的区域"
            ))
        
        return goals
    
    # 辅助方法
    def _find_safe_positions(self, agent, world_state) -> List[Tuple[int, int]]:
        """寻找安全位置"""
        safe_positions = []
        current_x, current_y = agent.position
        
        # 远离所有威胁的位置
        for x in range(world_state.game_map.width):
            for y in range(world_state.game_map.height):
                if self._is_position_safe(agent, world_state, (x, y)):
                    distance = self._calculate_distance((current_x, current_y), (x, y))
                    if distance <= 8:  # 在移动范围内
                        safe_positions.append((x, y))
        
        # 按距离排序，优先选择较近的安全位置
        safe_positions.sort(key=lambda pos: self._calculate_distance((current_x, current_y), pos))
        return safe_positions
    
    def _is_position_safe(self, agent, world_state, position) -> bool:
        """判断位置是否安全"""
        x, y = position
        
        # 检查是否有其他agent占据
        for other_agent in world_state.agents.values():
            if other_agent.agent_id != agent.agent_id and other_agent.position == position:
                return False
        
        # 检查周围是否有威胁
        for other_agent in world_state.agents.values():
            if other_agent.agent_id != agent.agent_id:
                distance = self._calculate_distance(position, other_agent.position)
                if distance <= 2:  # 攻击范围内
                    relationship = agent.relationships.get(other_agent.agent_id)
                    if relationship and relationship.score < 40:  # 敌对关系
                        return False
        
        return True
    
    def _find_nearest_resource(self, agent, world_state, resource_type) -> Optional[Tuple[int, int]]:
        """寻找最近的资源位置"""
        if resource_type == "food":
            return (4, 8)  # 假设餐厅在(4,8)
        elif resource_type == "water":
            return (4, 8)  # 假设餐厅也有水
        return None
    
    def _assess_nearby_threats(self, agent, world_state) -> List[Dict]:
        """评估附近的威胁"""
        threats = []
        
        for other_agent in world_state.agents.values():
            if other_agent.agent_id != agent.agent_id:
                relationship = agent.relationships.get(other_agent.agent_id)
                if relationship and relationship.score < 40:
                    distance = self._calculate_distance(agent.position, other_agent.position)
                    threat_level = (40 - relationship.score) * (5 - min(distance, 4))  # 距离越近威胁越大
                    
                    threats.append({
                        'agent': other_agent,
                        'distance': distance,
                        'threat_level': threat_level,
                        'relationship_score': relationship.score
                    })
        
        return threats
    
    def _find_escape_positions(self, agent, world_state, threat_agent) -> List[Tuple[int, int]]:
        """寻找逃离位置"""
        escape_positions = []
        current_x, current_y = agent.position
        threat_x, threat_y = threat_agent.position
        
        # 寻找远离威胁的位置
        for x in range(world_state.game_map.width):
            for y in range(world_state.game_map.height):
                distance_from_agent = self._calculate_distance((current_x, current_y), (x, y))
                distance_from_threat = self._calculate_distance((threat_x, threat_y), (x, y))
                
                if (distance_from_agent <= 8 and  # 在移动范围内
                    distance_from_threat > 3 and  # 远离威胁
                    not self._is_position_occupied(world_state, (x, y))):
                    escape_positions.append((x, y))
        
        # 按远离威胁的距离排序
        escape_positions.sort(key=lambda pos: -self._calculate_distance((threat_x, threat_y), pos))
        return escape_positions
    
    def _find_potential_allies(self, agent, world_state) -> List:
        """寻找潜在盟友"""
        potential_allies = []
        
        for other_agent in world_state.agents.values():
            if (other_agent.agent_id != agent.agent_id and 
                other_agent.role == agent.role):  # 同角色更容易建立联盟
                relationship = agent.relationships.get(other_agent.agent_id)
                if not relationship or relationship.score > 30:  # 非敌对关系
                    distance = self._calculate_distance(agent.position, other_agent.position)
                    if distance <= 2:  # 在对话范围内
                        potential_allies.append(other_agent)
        
        return potential_allies
    
    def _get_patrol_points(self, world_state) -> List[Tuple[int, int]]:
        """获取巡逻点"""
        # 监狱的关键巡逻点
        return [(1, 1), (7, 1), (1, 14), (7, 14), (4, 8)]  # 四角和餐厅
    
    def _get_prisoner_safe_areas(self, world_state) -> List[Tuple[int, int]]:
        """获取囚犯安全活动区域"""
        return [(2, 10), (6, 10), (4, 12)]  # 院子等相对安全的区域
    
    def _find_unexplored_areas(self, agent, world_state) -> List[Tuple[int, int]]:
        """寻找未探索区域"""
        # 简化实现：返回一些远离当前位置的区域
        current_x, current_y = agent.position
        unexplored = []
        
        exploration_points = [(0, 0), (8, 0), (0, 15), (8, 15), (4, 8)]
        for x, y in exploration_points:
            distance = self._calculate_distance((current_x, current_y), (x, y))
            if distance > 3:  # 相对较远的地方
                unexplored.append((x, y))
        
        return unexplored
    
    def _calculate_distance(self, pos1, pos2) -> int:
        """计算曼哈顿距离"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def _is_position_occupied(self, world_state, position) -> bool:
        """检查位置是否被占据"""
        for agent in world_state.agents.values():
            if agent.position == position:
                return True
        return False
    
    def _create_default_goal(self) -> Goal:
        """创建默认目标"""
        return Goal(
            goal_id="default_rest",
            name="休息观察",
            description="没有紧急需求，休息并观察环境",
            need_level=NeedLevel.EXPLORATION,
            priority_score=1,
            action_type="do_nothing",
            parameters={},
            reasoning="没有特别紧急的需求，选择休息观察"
        )