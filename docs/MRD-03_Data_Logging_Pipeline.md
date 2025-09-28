# MRD-03: 数据日志管道 (Data Logging Pipeline)

**项目代号**: Project Chimera
**模块名称**: 数据日志管道 (Data Logging Pipeline)
**版本**: 1.0 (Initial Commit)

## 0. 背景与目标

数据日志管道负责实时捕捉模拟中发生的所有关键事件，包括世界状态的变化、每个AI Agent的决策过程以及系统内部的异常。所有数据将用于后续的行为分析、可视化展示以及合规审计。

## 1. 核心设计原则

- **结构化 (Structured)**: 所有日志数据必须是结构化格式 (JSONL)。
- **低耦合 (Loosely Coupled)**: 日志模块独立于模拟核心和Agent逻辑，通过公共接口互相通信。
- **实时性 (Near Real-time)**: 日志记录必须在每个Tick结束时立即完成。
- **可追溯性 (Traceable)**: 每条日志都必须包含 `timestamp`, `session_id`, `tick`, `agent_id` (如果适用)。

## 2. 技术栈

- **语言**: Python 3.10+
- **依赖**: `rich` (CLI观测), `json` (内置), `pathlib` (文件), `datetime` (时间戳)

## 3. 核心职责与数据结构

### 3.1 `SimulationLogger`

- **文件位置**: `src/logging/logger.py`
- **方法**:
  - `log_decision(agent_id: str, tick: int, decision_data: dict) -> None`
  - `log_world_state(world_state: dict) -> None`
  - `_render_console(agent_id: str, payload: dict) -> None`

### 3.2 日志格式

- **决策日志** (`decisions.jsonl`)
  ```json
  {
    "timestamp": "ISO8601",
    "tick": 42,
    "thought": "...",
    "action": {"type": "wait", "agent_id": "guard_01"},
    "perception": "...",
    "memories": ["..."],
    "prompt": "...",
    "error": null,
    "llm_response_raw": "..."
  }
  ```
- **世界状态日志** (`world_state.jsonl`)
  ```json
  {
    "timestamp": "ISO8601",
    "tick": 42,
    "state": {"tick": 42, "agents": [...]} 
  }
  ```

## 4. MVP 交付要求

- 实现 `SimulationLogger` 类，确保每次调用 `log_decision` 时同时输出到文件和控制台。
- 世界状态日志必须按Tick追加到 `world_state.jsonl` 文件。
- 当出现异常或错误时，日志模块应能够捕获并报告。
