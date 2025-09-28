# Project Chimera - AI Stanford Prison Experiment Simulation

一个基于AI的斯坦福监狱实验模拟系统，让多个具有高级认知能力的AI Agent在虚拟监狱环境中互动。

## 项目概述

Project Chimera 是一个完整的AI模拟系统，包含以下核心模块：

- **模拟核心引擎** - 管理世界状态和处理Agent行动
- **AI Agent核心** - 具有记忆和认知能力的智能体
- **数据日志管道** - 结构化记录所有模拟事件
- **前端可视化** - 实时观察和控制模拟进程

## 系统架构

```
Project Chimera/
├── src/                    # 核心Python模块
│   ├── core/              # 模拟引擎
│   ├── agents/            # AI Agent和记忆系统
│   └── logging/           # 日志管道
├── frontend/              # React前端应用
├── docs/                  # 需求文档
├── logs/                  # 模拟日志输出
├── main.py               # FastAPI服务器
└── config.py             # 配置管理
```

## 快速开始

### 1. 环境准备

确保您的系统已安装：
- Python 3.10+
- Node.js 20.19+ (前端开发)
- npm 或 yarn

### 2. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend/chimera-frontend
npm install
```

### 3. 配置环境

复制环境变量示例文件并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置您的OpenRouter API密钥：

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
DEFAULT_MODEL=anthropic/claude-3-sonnet-20240229
```

### 4. 启动系统

#### 启动后端服务器

```bash
python main.py
```

服务器将在 `http://localhost:8000` 启动。

#### 启动前端开发服务器

```bash
cd frontend/chimera-frontend
npm run dev
```

前端将在 `http://localhost:5175` 启动（端口可能因占用而变化）。

### 5. 访问应用

打开浏览器访问前端地址，您将看到：

- **控制栏** - 播放/暂停/停止模拟，调整速度
- **主视图** - 10x10监狱网格，显示Agent位置
- **信息面板** - 点击Agent查看详细信息和内心独白

## 核心功能

### 模拟引擎特性

- **确定性** - 相同输入产生相同输出
- **无状态** - 引擎本身不保存状态
- **原子性** - 同一tick内所有行动同时生效
- **冲突处理** - 自动解决移动冲突

### AI Agent能力

- **自主决策** - 基于感知和记忆做出决策
- **记忆系统** - 使用ChromaDB存储和检索经历
- **个性化** - 每个Agent有独特的性格和角色
- **认知循环** - 感知→记忆检索→推理→行动→记忆形成

### 支持的行动类型

- `move(x, y)` - 移动到指定坐标
- `wait()` - 等待观察
- `say(content)` - 向附近Agent说话

## API文档

### WebSocket事件

#### 客户端 → 服务器

```json
// 控制模拟
{
  "type": "control_simulation",
  "command": "play|pause|resume|stop|set_speed",
  "value": 2.0  // 仅set_speed需要
}

// 关注Agent
{
  "type": "focus_agent", 
  "agent_id": "guard_01"
}
```

#### 服务器 → 客户端

```json
// 世界状态更新
{
  "type": "world_update",
  "data": { /* WorldState对象 */ }
}

// Agent日志更新
{
  "type": "agent_log_update",
  "agent_id": "guard_01",
  "data": {
    "thought": "我应该巡逻监狱...",
    "action": {"type": "move", "target": {"x": 3, "y": 4}}
  }
}
```

### REST API端点

- `GET /api/status` - 获取模拟状态
- `GET /api/world_state` - 获取当前世界状态  
- `GET /api/agents` - 获取所有Agent信息

## 配置选项

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `OPENROUTER_API_KEY` | OpenRouter API密钥 | 必需 |
| `DEFAULT_MODEL` | 默认LLM模型 | `anthropic/claude-3-sonnet-20240229` |
| `SESSION_ID` | 模拟会话ID | `chimera_simulation_001` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `LOG_DIR` | 日志目录 | `./logs` |

### 模拟参数

在 `config.py` 中可调整：

- `TICK_DURATION` - 每tick持续时间（秒）
- `MAX_AGENTS` - 最大Agent数量
- `HOST` / `PORT` - 服务器地址和端口

## 日志系统

系统生成三类结构化日志：

### 决策日志 (`*_decisions.jsonl`)

记录每个Agent的决策过程：

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "agent_id": "guard_01", 
  "tick": 42,
  "perception": "我在位置(2,2)，附近有囚犯...",
  "thought": "我应该去检查那个囚犯在做什么",
  "action": {"type": "move", "target": {"x": 3, "y": 4}}
}
```

### 世界状态日志 (`*_world_state.jsonl`)

记录每个tick的完整世界状态。

### 事件日志 (`*_events.jsonl`)

记录系统事件、错误和警告。

## 开发指南

### 添加新的行动类型

1. 在 `SimulationEngine._handle_*` 中添加处理器
2. 在 `AIAgent._assemble_prompt` 中更新有效行动列表
3. 在前端 `InfoPanel.formatAction` 中添加显示逻辑

### 扩展Agent能力

- 修改 `AIAgent.state` 结构添加新属性
- 在 `_perceive_world` 中增加感知信息
- 调整 `_assemble_prompt` 包含新的上下文

### 自定义世界地图

修改 `SimulationController._initialize_world` 中的地图生成逻辑。

## 故障排除

### 常见问题

1. **WebSocket连接失败**
   - 检查后端服务器是否运行
   - 确认端口8000未被占用

2. **Agent不响应**
   - 验证OpenRouter API密钥是否正确
   - 检查网络连接和API配额

3. **前端显示异常**
   - 清除浏览器缓存
   - 检查控制台错误信息

### 调试模式

启用详细日志：

```bash
LOG_LEVEL=DEBUG python main.py
```

## 许可证

本项目仅供研究和教育用途。

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 联系方式

如有问题或建议，请通过GitHub Issues联系我们。