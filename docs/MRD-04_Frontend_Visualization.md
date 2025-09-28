**项目代号**: Project Chimera
**模块名称**: 前端可视化层 (Frontend Visualization Layer)
**版本**: 1.3 (Final Detailed)

### **0. 项目背景与目标**

本项目旨在创建一个**简洁、直观、运行在浏览器上的Web用户界面**，让研究人员能够实时观察模拟的进行、追踪特定AI Agent的行为，并一窥其“内心思考”。

### **1. 核心设计原则**

  * **清晰的可观测性 (Clear Observability)**, **准实时更新 (Near Real-time)**, **彻底解耦 (Fully Decoupled)**, **MVP优先 (MVP First)**。

### **2. 技术栈**

  * **后端API服务器**: **FastAPI (Python)**
  * **前端**: **React (JavaScript/TypeScript)**, **HTML `<div>` + CSS Grid/Flexbox**
  * **通信协议**: **WebSockets**

### **3. API与数据契约**

后端主服务 (`main.py`) 负责实例化所有模块并运行主模拟循环。

**主模拟循环伪代码**

```python
# In main.py
logger = SimulationLogger(...)
agents = [AIAgent(...), AIAgent(...)]
engine = SimulationEngine()
current_state = ...

while True:
    if not paused:
        actions = []
        for agent in agents:
            # Pass logger to each agent
            action = agent.think(current_state, logger)
            actions.append(action)

        current_state = engine.calculate_next_state(current_state, actions)
        
        # Broadcast the new state to all connected clients
        await websocket_manager.broadcast(current_state)
```

#### **3.1 WebSocket 事件 (Events)**

  * **后端 -\> 前端**:
      * `world_update (dict)`: **核心事件**。在每个Tick结束后，后端向所有连接的前端广播完整的`WorldState` JSON对象。
      * `agent_log_update (dict)`: 当被“关注”的Agent产生新的日志时，后端可以主动推送这条日志的详细信息（尤其是`thought`字段）。
  * **前端 -\> 后端**:
      * `control_simulation (dict)`: 用户通过UI发送控制指令。例如: `{"command": "pause"}`, `{"command": "play"}`, `{"command": "set_speed", "value": 2}`。
      * `focus_agent (dict)`: 用户点击某个Agent时，前端通知后端希望“关注”这个Agent。例如: `{"agent_id": "prisoner_A"}`。
  * **注意**: 后端服务器需要为每个WebSocket连接维护一个状态，以记录该客户端当前“关注”的是哪个`agent_id`。

### **4. 功能需求：用户界面 (UI)**

整个界面采用经典的三栏式布局。

#### **4.1 左侧：主视图 (Main View)**

  * **功能**: 渲染模拟世界的主网格。
  * **实现**:
      * 使用CSS Grid动态生成一个`N x M`的网格容器。
      * `map`中的`Wall`等对象渲染为带特定背景色的格子。
      * `agents`列表中的每个Agent，根据其`position`和`role`渲染为一个带特定颜色/图标的`<div>`，并显示其ID。

#### **4.2 右侧：信息面板 (Info Panel)**

  * **功能**: 当用户在主视图中点击一个Agent时，此面板显示该Agent的详细信息。
  * **实现**:
      * **Agent ID**: 显示被选中Agent的ID和角色。
      * **当前状态**: 以列表形式显示Agent的内部状态。
      * **当前行动**: 显示Agent当前正在执行的行动。
      * **内心独白 (Inner Monologue)**:
          * **【核心功能】** 这是一个滚动文本区域，用于显示该Agent最新一条日志中的`thought`字段内容。
          * 当后端推送`agent_log_update`事件时，新的“想法”会追加到这个区域的顶部。

#### **4.3 顶部：控制面板 (Control Panel)**

  * **功能**: 提供对模拟进程的全局控制。
  * **实现**:
      * **播放/暂停按钮**: 发送`play`/`pause`控制指令。
      * **模拟速度**: 一个下拉菜单或一组按钮（1x, 2x, 5x），发送`set_speed`指令。
      * **状态显示**: 显示当前的 `Tick` 数量和 `session_id`。

### **5. MVP范围与交付要求**

  * **后端**:
      * 交付一个`main.py`（或`api_server.py`），使用FastAPI搭建，实现WebSocket端点和可控的主模拟循环。
  * **前端**:
      * 交付一个基础的React应用，实现三栏式布局，通过WebSocket连接后端并渲染数据。

### **6. 给AI IDE的启动指令 (Prompt for AI IDE)**

  * **注意**: 这个模块包含后端服务和前端应用两部分，最好分两次或在两个独立的会话中进行。

#### **Prompt 1: 后端API服务器**

> **Project Context:** We are building the API server for our "Project Chimera" AI simulation. This server runs the main simulation loop and communicates with a web-based frontend using WebSockets.
>
> **Task:**
>
> Create a Python file named `main.py` using the **FastAPI** framework.
>
> 1.  The server should define a WebSocket endpoint at `/ws`.
> 2.  Upon startup, it should instantiate our existing modules: `SimulationEngine`, `AIAgent`, and `SimulationLogger`.
> 3.  Implement a main simulation loop in an `async` function. This loop should:
>     a. Collect actions from all agents by calling their `think()` method (and passing the logger instance).
>     b. Calculate the next world state using the `engine.calculate_next_state()` method.
>     c. Broadcast the complete new `world_state` JSON to all connected WebSocket clients.
>     d. Handle `play`/`pause`/`set_speed` commands received from clients via WebSocket to control the loop's execution.
> 4.  The server should also serve a static directory `./static` where our frontend build files will be located.

#### **Prompt 2: 前端React应用**

> **Project Context:** We are building the frontend for our "Project Chimera" AI simulation using React. This web app will visualize the simulation in real-time by connecting to a FastAPI backend via WebSockets.
>
> **Task:**
>
> Initialize a new React application (you can use Vite or Create React App). Then, implement the following components:
>
> 1.  **Main App Layout:** Create a main component that sets up a three-panel UI: a top control bar, a main grid view on the left, and an info panel on the right.
> 2.  **WebSocket Connection:** Implement a hook or service to manage the WebSocket connection to the backend server's `/ws` endpoint. It should handle incoming messages, especially the `world_update` event.
> 3.  **GridView Component:** This component receives the `map` and `agents` data from the `world_state`. It should render the grid and the agents on it using CSS Grid. Agents can be simple `<div>` elements. Implement a feature where clicking on an agent sets it as the "selected agent" in the global state.
> 4.  **InfoPanel Component:** This component receives the data of the "selected agent". It should display the agent's ID, role, status, and most importantly, a text area for their "Inner Monologue" (the `thought` from their latest log).
> 5.  **ControlBar Component:** This component should have Play/Pause buttons that send the corresponding `control_simulation` commands through the WebSocket. It should also display the current tick number from the `world_state`.