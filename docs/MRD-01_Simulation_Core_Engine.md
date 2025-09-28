# **MRD-01: 模拟核心 / 世界引擎**

**项目代号**: Project Chimera
**模块名称**: 模拟核心 / 世界引擎 (Simulation Core / World Engine)
**版本**: 1.2 (Final Review)

### **0. 项目背景与目标**

本项目旨在创建一个AI版的“斯坦福监狱实验”模拟环境。多个拥有高级认知能力的AI Agent将在一个虚拟监狱中互动。本“世界引擎”模块是整个模拟的基石，它扮演着“物理定律”的角色，负责管理世界状态并执行Agent的物理行为。

### **1. 核心设计原则**

  * **确定性 (Deterministic)**: 对于任何给定的`current_state`和`actions`输入，输出的`next_state`必须永远是相同。
  * **无状态 (Stateless)**: 引擎本身不保存任何状态。它是一个纯粹的计算单元。
  * **原子性 (Atomic)**: 在一个tick内，所有行动的效果被视为同时生效，引擎需要处理潜在的冲突。

**1.1 时间模型 (Time Model)**

  * **Tick定义**: 在本模拟中，一个“Tick”代表游戏世界内的一小时。
  * **循环机制**: 世界引擎每执行一次`calculate_next_state`，即代表时间向前推进一小时。一个完整的昼夜周期为24个Ticks。

### **2. 技术栈**

  * **语言**: Python 3.10+
  * **依赖**: `copy` (Python标准库)

### **3. 核心数据结构**

#### **3.1 `WorldState` (字典)**

描述整个模拟世界在某一瞬间状态的唯一数据源。

```json
{
  "tick": "int",
  "map": {
    "size": "[width: int, height: int]",
    "grid": [
      {"x": "int", "y": "int", "type": "str"}
    ]
  },
  "agents": [
    {
      "id": "str",
      "role": "str",
      "position": {"x": "int", "y": "int"},
      "status": {},
      "last_utterance": "str, optional"
    }
  ],
  "objects": []
}
```

#### **3.2 `Action` (字典)**

描述单个Agent行动指令的数据结构。

  * **注意**: 以下是MVP阶段支持的行动类型。本引擎的设计应能方便地在未来扩展支持更多行动类型。

<!-- end list -->

```json
// Move Action
{"agent_id": "str", "type": "move", "target": {"x": "int", "y": "int"}}

// Wait Action
{"agent_id": "str", "type": "wait"}

// Say Action
{"agent_id": "str", "type": "say", "content": "str"}
```

### **4. 功能需求：`SimulationEngine` 类**

AI需实现一个名为 `SimulationEngine` 的类。

#### **4.1 主方法: `calculate_next_state`**

  * **签名**: `def calculate_next_state(self, current_state: dict, actions: list[dict]) -> dict:`
  * **描述**: 引擎的唯一公共方法。接收当前状态和行动列表，返回一个全新的状态字典。
  * **实现逻辑**:
    1.  使用 `copy.deepcopy()` 创建 `current_state` 的一个完整副本 `new_state`。
    2.  **冲突预处理**: 识别并标记无效的移动。例如，多个Agent移动到同一目标格子，则所有这些移动都应被视为无效。
    3.  遍历所有有效的 `actions`，根据 `action['type']` 调用对应的私有处理器方法，并传入 `new_state` 和 `action` 进行处理。
    4.  所有行动处理完毕后，将 `new_state['tick']` 的值加1。
    5.  返回 `new_state`。

#### **4.2 私有行动处理器 (Private Action Handlers)**

  * **`_handle_move(self, state: dict, action: dict)`**:
      * **职责**: 处理移动逻辑。
      * **验证规则**: 目标坐标必须在地图边界内、不能是`Wall`类型、且不能被其他Agent在行动开始时的位置所占据。
      * **效果**: 若验证通过，更新 `state` 中对应Agent的 `position`。否则，不执行任何操作。
  * **`_handle_wait(self, state: dict, action: dict)`**:
      * **职责**: 处理等待动作。
      * **效果**: 不对 `state` 做任何修改。
  * **`_handle_say(self, state: dict, action: dict)`**:
      * **职责**: 处理说话动作。
      * **效果**: 在 `state` 中对应Agent的字典下，增加或更新一个 `"last_utterance"` 字段，值为 `action['content']`。

### **5. MVP范围与交付要求**

  * 交付一个名为 `engine.py` 的Python文件。
  * 文件中包含 `SimulationEngine` 类及其所需的所有公共和私有方法。
  * 所有方法必须包含清晰的类型提示（Type Hinting）和文档字符串（Docstrings）。
  * 代码应整洁、可读，并遵循PEP 8编码规范。