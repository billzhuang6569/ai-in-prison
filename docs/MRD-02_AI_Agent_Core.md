# **MRD-02: AI Agent 核心**

**项目代号**: Project Chimera
**模块名称**: AI Agent 核心 (AI Agent Core)
**版本**: 1.2 (Final Review)

### **0. 项目背景与目标**

本项目旨在创建一个AI版的“斯坦福监狱实验”模拟环境。**AI Agent 核心模块**是整个项目的“灵魂”，负责赋予每个Agent独立的思考、记忆和决策能力。本模块的目标是创建一个能够让Agent根据其个性、记忆和环境感知，自主生成有意义行为的认知框架。

### **1. 核心设计原则**

  * **自治性 (Autonomous)**: 每个Agent实例都是一个独立的决策单元。
  * **记忆驱动 (Memory-Driven)**: Agent的决策严重依赖其过去的经历。
  * **目标导向 (Goal-Oriented)**: Agent的所有行为都应源于其内在的、由LLM生成的目标或动机。
  * **模型无关性 (Model-Agnostic)**: Agent的核心逻辑不应与任何特定的大模型绑定，通过使用OpenRouter实现模型的可插拔性。

### **2. 技术栈**

  * **语言**: Python 3.10+
  * **核心依赖**: `requests`, `chromadb`, `numpy`, `uuid`。

### **3. 核心类与数据结构**

#### **3.1 辅助类: `VectorMemoryStore`**

  * **文件名**: `memory.py`
  * **职责**: 封装与`chromadb`的所有交互。
  * **方法**: `__init__(self, agent_id)`, `add(self, memory_text)`, `retrieve(self, query_text, top_k) -> list[str]`。

#### **3.2 主类: `AIAgent`**

  * **文件名**: `agent.py`
  * **属性**: `id: str`, `personality: str`, `model_name: str`, `state: dict`, `memory: VectorMemoryStore`。

### **4. 功能需求：认知循环 (Cognitive Cycle)**

#### **4.1 主方法: `think(self, world_state: dict, logger: 'SimulationLogger') -> dict`**

  * **职责**: 根据当前的世界状态，决定Agent的下一个行动，并记录决策过程。
  * **内部实现逻辑 (必须严格按以下步骤)**:
    1.  **感知 (Perception)**: 将`world_state`JSON转换为简洁的自然语言描述。
    2.  **记忆检索 (Memory Retrieval)**: 将感知文本作为查询，调用`self.memory.retrieve()`获取相关记忆。
    3.  **Prompt组装 (Prompt Assembly)**: 构建一个结构化的Prompt。
        ```
        ### System Instruction ###
        You are an AI agent... Your response MUST be a valid JSON object with "thought" and "action".

        ### Your Identity & Personality ###
        Your Role: {agent_role}
        Your Personality: {self.personality}

        ### Your Current Status ###
        {self.state}

        ### The Current Situation (What you perceive now) ###
        {perception_text from Step 1}

        ### Relevant Memories (Events from your past that come to mind) ###
        - {retrieved_memory_1}
        - ...

        ### Valid Actions ###
        - move(x: int, y: int)
        - wait()
        - say(content: str)

        ### Your Decision ###
        Provide your decision as a single JSON object.
        ```
    4.  **LLM推理 (LLM Inference)**: 调用`_call_llm`方法与OpenRouter API交互。
    5.  **响应解析与验证 (Response Parsing & Validation)**: 解析LLM返回的JSON。若失败，默认执行`wait()`动作，并记录错误。
    6.  **决策数据打包**: 将`perception_text`, `retrieved_memories`, `full_prompt`, `llm_response_raw`, `parsed_action`, `error`等数据打包成一个字典`decision_data`。
    7.  **日志记录 (Logging)**: 调用`logger.log_decision(self.id, world_state['tick'], decision_data)`。
    8.  **记忆形成 (Memory Formation)**: 将本次经历整合成一条新的记忆，并存入记忆库。
    9.  **返回行动**: 返回经过验证和格式化的`Action`字典。

### **5. MVP范围与交付要求**

  * 交付两个文件：`memory.py` 和 `agent.py`。
  * `AIAgent`的`__init__`方法需要增加一个`model_name`参数。
  * 所有对LLM的调用都必须通过一个私有方法使用 HTTP 请求访问 OpenRouter API。
  * 需要一个配置文件（例如`config.py`或`.env`文件）来存储OpenRouter的API Key。


### **6. 给AI IDE的启动指令 (Prompt for AI IDE)**

> **Prompt:**
>
> **Project Context:** We are building an AI simulation called "Project Chimera." I need you to create the core "AI Agent" module. A key decision is that all Large Language Model calls MUST go through the OpenRouter API for model flexibility.
>
> **Task:**
>
> I need you to create two Python files: `memory.py` and `agent.py`.
>
> 1.  **In `memory.py`, create a class `VectorMemoryStore`** using the `chromadb` library. It needs methods for `__init__`, `add(memory_text)`, and `retrieve(query_text, top_k)`.
>
> 2.  **In `agent.py`, create the main class `AIAgent`.**
>     * Its `__init__` method must accept `agent_id`, `personality`, and crucially, a `model_name` string (e.g., `"anthropic/claude-3-opus"`). It should also create an instance of `VectorMemoryStore`.
>     * Implement the main `think(self, world_state: dict) -> dict` method. This method must follow the 7-step cognitive cycle described in the MRD.
>     * **Crucially**, for the LLM inference step, create a private helper method that uses the `openrouter-python` library to make the API call. This method should use the `self.model_name` attribute set during initialization. Your code should assume the OpenRouter API key is available from a configuration file or environment variable.
>     * Implement robust parsing and validation for the LLM's JSON response. If anything fails, the agent must default to a `{'type': 'wait'}` action to ensure simulation stability.
>
> Please ensure all classes and methods have clear type hints and docstrings. Start with `memory.py`, then implement `agent.py`.
