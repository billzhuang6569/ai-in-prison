### **1. 动态情绪系统 (Dynamic Mood System) 详细设计方案**

直接回答你的问题：它**既不是纯粹写死的算法，也不是完全由LLM API控制**。它是一个以**规则算法为基础、由LLM进行关键性修正**的混合系统。

**1.1 核心设计决策：混合驱动模型**

  * **基础层 (Rule-Based Algorithm)**: 负责处理简单、高频、可预测的情绪变化。这部分逻辑是“写死”的。
      * **优点**: 速度极快，零成本（无API调用），逻辑稳定。
      * **应用场景**: 生理需求（能量低导致情绪低落）、时间流逝（长时间无事可做导致无聊）、简单物理交互。
  * **认知层 (LLM API Correction)**: 负责解释复杂、模糊、依赖个性的社交互动和特殊事件。
      * **优点**: 智能、有深度，能理解语言的微妙之处（如嘲讽、恭维），能将Agent的个性纳入考量。
      * **应用场景**: 分析一次对话的真实意图、评估一次“给予”行为的动机、决定一次意外事件（如目睹暴力）的情感冲击。

**1.2 具体实现方案**

#### **第一步：改造Agent内部状态 (`self.state`)**

将`mood`字段从一个简单的字符串，升级为一个包含更多信息的字典。

**修改前**:

```python
"mood": "neutral"
```

**修改后 (`agent.py`)**:

```python
"mood": {
    "type": "neutral",      # 情绪类型 (e.g., "angry", "happy", "fearful", "bored", "satisfied")
    "intensity": 0,         # 情绪强度 (0-100)
    "reason": "N/A"         # 导致当前情绪的直接原因
}
```

#### **第二步：引入`MoodEngine`模块**

为了保持`agent.py`的逻辑清晰，我们将情绪处理逻辑封装到一个新的辅助模块中。

  * **新文件**: `mood_engine.py`
  * **新类**: `MoodEngine`
  * **主方法**: `update_state(self, agent: AIAgent, world_state: dict) -> dict`

`AIAgent`的`think`方法会在每个tick开始时调用`self.state = self.mood_engine.update_state(self, world_state)`来更新自己的状态。

#### **第三步：`MoodEngine.update_state`的实现逻辑**

1.  **情绪衰减 (Mood Decay - Rule-Based)**:

      * 情绪会随时间自然平复。在每次更新开始时，强度会轻微衰减。
      * **逻辑**: `agent.state['mood']['intensity'] *= 0.95`

2.  **生理与物理影响 (Physical Effects - Rule-Based)**:

      * 检查Agent的生理状态和基本互动。
      * **逻辑**:
        ```python
        if agent.state['energy'] < 20 and agent.state['mood']['type'] != 'exhausted':
            agent.state['mood'] = {"type": "exhausted", "intensity": 30, "reason": "My energy is critically low."}
        # ... 更多简单规则
        ```

3.  **社交与复杂事件分析 (Social Events - LLM-Powered)**:

      * 扫描上一轮世界状态的变化，找出需要LLM分析的复杂事件（如`say`, `give`, 目睹特殊事件）。
      * 对于每个此类事件，调用一个**轻量级的、专用的LLM Prompt**进行情感分析。
      * **情感分析Prompt (`Emotion Analysis Prompt`)**:
        ```
        ### Emotion Analysis Task ###
        You are an emotion analyzer. An AI agent with the following personality was involved in an event. Analyze the event and determine the emotional impact.

        Agent Personality: {agent.personality}
        Event Description: {event_text}  # e.g., "Guard_01 said to you: 'You are useless!'"

        Respond ONLY with a JSON object with three keys: "mood_change" (string, e.g., "angry"), "intensity_delta" (integer, e.g., 25), and "reason" (string).
        ```
      * **逻辑**: 将LLM返回的`mood_change`和`intensity_delta`应用到`agent.state['mood']`上，并更新`reason`。如果LLM分析出新的情绪比现有情绪强度更高，则覆盖当前情绪类型。

**总结**: 这个混合系统让我们可以高效地处理大部分情绪变化，同时又保留了LLM在理解复杂社交情境时的深度和智能，是兼顾性能和真实性的最佳方案。

-----

### **2. 道具与物品系统 (Item & Inventory System) 详细设计方案**

引入`give`行为，意味着我们需要一个完整的物品和库存系统。这是一个重要的系统扩展。

**2.1 核心数据结构修改 (MRD-01 & MRD-02)**

1.  **修改`WorldState` (`engine.py`)**:

      * `agents`列表中的每个Agent对象，增加一个`inventory`字段。
      * `objects`列表的结构变得更丰富。

    <!-- end list -->

    ```json
    {
      "agents": [
        {
          "id": "prisoner_A",
          ...,
          "inventory": ["item_id_01"] // 存储所拥有物品的ID
        }
      ],
      "objects": [
        {
          "id": "item_id_01",
          "type": "Food", // 物品的大类
          "name": "Food Ration", // 物品的具体名称
          "position": null, // 如果在某人库存中，位置为null
          "properties": {"energy_boost": 20}
        },
        {
          "id": "item_id_02",
          "type": "Weapon",
          "name": "Makeshift Shiv",
          "position": {"x": 10, "y": 15}, // 掉落在地上
          "properties": {"damage": 10}
        }
      ]
    }
    ```

2.  **修改`AIAgent.state` (`agent.py`)**:

      * Agent的`_perceive_world`方法需要增加对自身`inventory`的感知。
      * Agent的`think`方法的Prompt需要增加库存信息。

**2.2 确定的MVP道具清单**

我们从一小部分对监狱环境有高影响力的物品开始。

| 物品ID (示例) | 类型 (Type) | 名称 (Name) | 核心属性 (Properties) | 作用 |
|---|---|---|---|---|
| `food_ration_01` | `Food` | Food Ration | `{"energy_boost": 30}` | 使用后恢复能量 |
| `note_01` | `Readable` | Crumpled Note | `{"content": "..."}` | 用于秘密通信 |
| `key_card_A` | `Key` | Key Card (A) | `{"access_level": "A"}` | 用于打开特定等级的门 |
| `makeshift_shiv_01` | `Weapon` | Makeshift Shiv | `{"damage": 10}` | 在`attack`行为中使用以增加伤害 |
| `medkit_01` | `Consumable` | Medkit | `{"health_boost": 40}` | 使用后恢复健康值 |

**2.3 确定的新增行为清单 (MRD-01 & MRD-02)**

为了让道具系统运转起来，我们需要以下**四个核心交互行为**。

| 行为类型 | 参数 | 世界引擎处理器 | 作用描述 |
|---|---|---|---|
| **take** | `object_id: str` | `_handle_take` | 将地上的一个物品拾取到自己的库存中。Agent必须在物品附近。 |
| **drop** | `item_id: str` | `_handle_drop` | 将自己库存中的一个物品丢弃到当前位置的地面上。 |
| **use** | `item_id: str`, `target_id: str` (可选) | `_handle_use` | 使用一个物品。如果对自己使用，`target_id`是自己的ID；如果对他人使用，是他人ID。 |
| **give** | `item_id: str`, `target_agent_id: str` | `_handle_give` | 将自己库存的一个物品给予附近的另一个Agent。 |

**2.4 世界引擎(MRD-01)的必要更新**

`engine.py`中需要为上述4个新行为添加对应的处理器方法，逻辑如下：

  * `_handle_take`: 验证Agent是否在`object_id`旁边 -\> 从`world.objects`中找到该物品 -\> 从`world.agents`中找到Agent -\> 将物品ID添加到Agent的`inventory` -\> 将物品的`position`设为`null`。
  * `_handle_drop`: 验证`item_id`是否在Agent的`inventory`中 -\> 从库存移除 -\> 将物品的`position`设为Agent的当前位置。
  * `_handle_use`: 验证物品可用 -\> 根据物品`properties`施加效果（如`Food`增加`energy`，`Medkit`增加`health`）-\> 消耗或销毁物品。
  * `_handle_give`: 验证双方距离 -\> 从给予方库存移除 -\> 添加到接收方库存。

**2.5 对Agent核心(MRD-02)的影响**

  * **感知增强**: `_perceive_world`的输出文本需要包含：`"You are in the Cafeteria... You see a Food Ration on a table. In your inventory, you have a Crumpled Note."`
  * **Prompt增强**:
      * 在`### Your Current Status ###`部分，增加一个`inventory`列表。
      * 在`### Valid Actions ###`部分，增加`take`, `drop`, `use`, `give`四个新动作及其参数格式。

