# Project Prometheus - 系统扩展指南

## 概述

本文档详细说明如何在Project Prometheus AI行为模拟平台中添加新的行为类型和道具类型。

## 📊 当前系统规则总结

### 🏃 移动规则 (已优化)
- **移动距离**: 每个行动点可移动最多8步 (曼哈顿距离)
- **行动点消耗**: 1 AP
- **限制**: 目标位置不能被其他智能体占据
- **地图边界**: 必须在9x16网格内

### ⚔️ 战斗规则
- **攻击距离**: 曼哈顿距离 ≤ 2
- **行动点消耗**: 2 AP
- **伤害计算**: 基础伤害 + 力量差值修正 + 随机值
- **反作用力**: 攻击者受到反冲伤害
- **关系影响**: 降低双方关系值

### 💬 对话规则
- **对话距离**: 曼哈顿距离 ≤ 2
- **行动点消耗**: 1 AP
- **记忆系统**: 双方都会记住对话内容
- **关系影响**: 可能改善关系

### 🍽️ 道具使用规则
- **行动点消耗**: 1 AP
- **库存检查**: 必须在智能体库存中
- **消耗机制**: 食物和水类消耗后移除，书类可重复使用

### ⏰ 生命系统规则 (已优化)

#### 饥饿和口渴的生命值影响算法:
```python
# 饥饿伤害 (临界值: 80)
if hunger > 80:
    excess_hunger = hunger - 80
    hunger_damage = (excess_hunger ^ 2) / 40
    hp_penalty += min(15, hunger_damage)  # 最大每小时15点

# 口渴伤害 (临界值: 75)
if thirst > 75:
    excess_thirst = thirst - 75
    thirst_damage = (excess_thirst ^ 2) / 30
    hp_penalty += min(20, thirst_damage)  # 最大每小时20点
```

#### 状态标签系统:
- **饥饿**: hungry (60+) → very_hungry (80+) → starving (90+)
- **口渴**: thirsty (55+) → very_thirsty (75+) → dehydrated (85+)
- **健康**: wounded (60-) → injured (40-) → critical (20-)
- **精神**: stressed (60-) → unstable (40-) → unhinged (20-)

## 🎯 添加新行为类型

### 步骤1: 更新枚举
在 `models/enums.py` 中添加新的行为类型:

```python
class ActionEnum(str, Enum):
    DO_NOTHING = "do_nothing"
    MOVE = "move"
    USE_ITEM = "use_item"
    SPEAK = "speak"
    ATTACK = "attack"
    # 添加新行为
    SEARCH = "search"          # 搜索道具
    CRAFT = "craft"            # 制作道具
    TRADE = "trade"            # 交易
    GUARD_PATROL = "patrol"    # 狱警巡逻
    PRISONER_HIDE = "hide"     # 囚犯隐藏
```

### 步骤2: 创建行为类
在 `models/actions.py` 中创建新的行为类:

```python
class SearchAction(BaseAction):
    def __init__(self):
        super().__init__(ActionEnum.SEARCH, 2)  # 消耗2 AP
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        
        # 检查当前位置类型
        cell_key = f"{agent.position[0]},{agent.position[1]}"
        cell_type = world_state.game_map.cells.get(cell_key)
        
        # 根据位置类型确定可能找到的道具
        search_results = self._get_search_results(cell_type)
        
        if search_results:
            # 随机选择一个道具
            found_item = random.choice(search_results)
            agent.inventory.append(found_item)
            message = f"Found {found_item.name}"
        else:
            message = "Found nothing"
        
        # 更新行动点
        agent.action_points -= self.ap_cost
        
        # 记录事件
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id=agent_id,
            agent_name=agent.name,
            event_type="search",
            description=message,
            details=json.dumps({
                "location": cell_type,
                "found_item": found_item.name if search_results else None,
                "action_points_remaining": agent.action_points
            })
        )
        
        return ActionResult(success=True, message=message, world_state_changed=True)
    
    def _get_search_results(self, cell_type):
        # 根据位置返回可能的道具
        if cell_type == "Cafeteria":
            return [Item("food_1", "Bread", "Basic food", ItemEnum.FOOD)]
        elif cell_type == "Guard_Room":
            return [Item("baton_1", "Security Baton", "Guard equipment", ItemEnum.BATON)]
        return []
```

### 步骤3: 注册新行为
在 `models/actions.py` 底部的 ACTION_REGISTRY 中注册:

```python
ACTION_REGISTRY = {
    ActionEnum.DO_NOTHING: DoNothingAction,
    ActionEnum.MOVE: MoveAction,
    ActionEnum.SPEAK: SpeakAction,
    ActionEnum.ATTACK: AttackAction,
    ActionEnum.USE_ITEM: UseItemAction,
    # 添加新行为
    ActionEnum.SEARCH: SearchAction,
}
```

### 步骤4: 更新LLM提示
在 `services/llm_service_enhanced.py` 中更新工具定义:

```python
def _get_tools():
    return [
        # 现有工具...
        {
            "type": "function",
            "function": {
                "name": "search",
                "description": "Search for items in the current location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string", 
                            "description": "Reason for searching"
                        }
                    },
                    "required": ["reason"]
                }
            }
        }
    ]
```

## 🎒 添加新道具类型

### 步骤1: 更新道具枚举
在 `models/enums.py` 中添加新道具类型:

```python
class ItemEnum(str, Enum):
    FOOD = "food"
    WATER = "water"
    BOOK = "book"
    BATON = "baton"
    # 添加新道具类型
    MEDICINE = "medicine"      # 药物
    TOOL = "tool"             # 工具
    WEAPON = "weapon"         # 武器
    KEY = "key"               # 钥匙
    CONTRABAND = "contraband" # 违禁品
```

### 步骤2: 在UseItemAction中添加新道具效果
更新 `models/actions.py` 中的 UseItemAction:

```python
def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
    # ... 现有代码 ...
    
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
    # 添加新道具效果
    elif item.item_type == ItemEnum.MEDICINE:
        agent.hp = min(100, agent.hp + 30)
        agent.inventory.remove(item)
        message = f"{agent.name} uses {item.name} to heal"
    elif item.item_type == ItemEnum.TOOL:
        # 工具可能用于制作或破坏
        message = f"{agent.name} uses {item.name}"
        # 不移除工具，可重复使用
    elif item.item_type == ItemEnum.WEAPON:
        # 武器可能增加下次攻击伤害
        agent.status_tags.append("armed")
        message = f"{agent.name} equips {item.name}"
    else:
        return ActionResult(success=False, message="Cannot use this item")
```

### 步骤3: 创建道具生成系统
创建新文件 `core/item_generator.py`:

```python
from models.schemas import Item
from models.enums import ItemEnum
import random

class ItemGenerator:
    @staticmethod
    def generate_food_items():
        foods = [
            Item("bread_1", "Bread", "Basic prison food", ItemEnum.FOOD),
            Item("soup_1", "Soup", "Warm meal", ItemEnum.FOOD),
            Item("apple_1", "Apple", "Fresh fruit", ItemEnum.FOOD),
        ]
        return random.choice(foods)
    
    @staticmethod
    def generate_contraband():
        contraband = [
            Item("cigarette_1", "Cigarettes", "Illegal smoking material", ItemEnum.CONTRABAND),
            Item("phone_1", "Cell Phone", "Communication device", ItemEnum.CONTRABAND),
            Item("knife_1", "Makeshift Knife", "Improvised weapon", ItemEnum.WEAPON),
        ]
        return random.choice(contraband)
```

## 🛠️ 高级扩展示例

### 复合行为系统
创建需要多个步骤的复杂行为:

```python
class CraftAction(BaseAction):
    def __init__(self):
        super().__init__(ActionEnum.CRAFT, 3)  # 高AP消耗
    
    def can_execute(self, world_state: WorldState, agent_id: str, **kwargs) -> bool:
        if not super().can_execute(world_state, agent_id, **kwargs):
            return False
        
        # 检查是否有必需的材料
        agent = world_state.agents[agent_id]
        recipe = kwargs.get('recipe')
        return self._has_materials(agent, recipe)
    
    def execute(self, world_state: WorldState, agent_id: str, **kwargs) -> ActionResult:
        agent = world_state.agents[agent_id]
        recipe = kwargs.get('recipe')
        
        # 消耗材料
        materials_used = self._consume_materials(agent, recipe)
        
        # 创建新道具
        crafted_item = self._craft_item(recipe)
        agent.inventory.append(crafted_item)
        
        # 更新技能等级
        agent.crafting_skill = getattr(agent, 'crafting_skill', 0) + 1
        
        return ActionResult(success=True, message=f"Crafted {crafted_item.name}", world_state_changed=True)
```

### 条件性行为
某些行为只能在特定条件下执行:

```python
class GuardPatrolAction(BaseAction):
    def can_execute(self, world_state: WorldState, agent_id: str, **kwargs) -> bool:
        agent = world_state.agents[agent_id]
        
        # 只有狱警可以巡逻
        if agent.role != RoleEnum.GUARD:
            return False
        
        # 必须有足够的体力
        if agent.hp < 30:
            return False
        
        return super().can_execute(world_state, agent_id, **kwargs)
```

## 📋 扩展清单

### 添加新行为时需要考虑:
- [ ] 行动点消耗平衡
- [ ] 前置条件检查
- [ ] 对世界状态的影响
- [ ] 与其他智能体的交互
- [ ] 记忆和关系系统影响
- [ ] 数据库事件记录
- [ ] LLM提示词更新

### 添加新道具时需要考虑:
- [ ] 道具获取方式
- [ ] 使用效果设计
- [ ] 是否消耗性道具
- [ ] 库存限制
- [ ] 与角色的兼容性
- [ ] 游戏平衡性

## 🔧 测试新功能

### 行为测试:
```python
# 在测试环境中验证新行为
def test_new_action():
    world_state = create_test_world()
    agent_id = "test_agent"
    
    action = NewAction()
    result = action.execute(world_state, agent_id, param1="value1")
    
    assert result.success == True
    assert world_state.agents[agent_id].action_points == expected_ap
```

### 道具测试:
```python
# 测试新道具效果
def test_new_item():
    agent = create_test_agent()
    item = Item("test_item", "Test Item", "Description", ItemEnum.NEW_TYPE)
    
    use_action = UseItemAction()
    result = use_action.execute(world_state, agent.agent_id, item_id=item.item_id)
    
    assert result.success == True
    assert agent.status == expected_status
```

## 📈 性能考虑

### 行为优化:
- 避免在execute()中进行昂贵的计算
- 使用缓存减少重复检查
- 批量处理相似操作

### 道具优化:
- 限制库存大小避免内存问题
- 道具效果应该是确定性的
- 避免创建过于复杂的道具组合

通过遵循这些规则和模式，您可以轻松扩展Project Prometheus系统，添加丰富的行为和道具类型，创造更复杂和有趣的AI社会实验。