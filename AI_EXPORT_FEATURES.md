# AI决策数据导出功能说明

## 概述

Project Prometheus现在支持完整的AI决策数据导出，研究人员可以获取AI agent每一轮的完整思考过程和决策数据，用于深度分析AI行为模式。

## 导出功能位置

### 1. 控制面板 (ControlPanel)
在左侧控制面板的"数据导出"部分，提供三种导出选项：

- **导出 CSV** (蓝色)：增强版CSV，包含13列数据
  - 完整事件记录 + AI决策信息
  - 包含：基础事件信息 + AI_Prompt_Content + AI_Thinking_Process + AI_Decision

- **AI决策数据** (紫色)：专门的AI分析数据，包含12列
  - 仅包含AI决策事件
  - 详细的prompt内容和thinking过程
  - 适合深度AI行为分析

- **导出 JSON** (绿色)：机器可读的结构化数据
  - 同样包含完整的AI决策信息
  - 适合程序化分析

### 2. AI Prompt监控面板 (PromptPanel)  
在右侧AI Prompt监控面板中：

- 选择特定Agent后，会出现"📊 导出此Agent的AI决策数据"按钮
- 可以导出单个Agent的AI决策历史数据
- 按session和agent筛选数据

## 数据结构说明

### 标准CSV导出包含字段：
1. ID, Session ID, Day, Hour, Minute
2. Agent ID, Agent Name, Event Type 
3. Description, Details, Timestamp
4. **AI_Prompt_Content** - 完整的AI prompt内容
5. **AI_Thinking_Process** - AI的思考过程
6. **AI_Decision** - AI的最终决策

### 专用AI决策CSV包含字段：
1. ID, Session ID, Day, Hour, Minute
2. Agent ID, Agent Name
3. **AI_Decision** - 决策内容
4. **Decision_Parameters** - 决策参数 
5. Timestamp
6. **Full_Prompt_Content** - 完整prompt
7. **Thinking_Process** - 完整思考过程

## 技术实现

### 后端增强
- 数据库添加AI决策字段：`ai_prompt_content`, `ai_thinking_process`, `ai_decision`
- 新增API端点：`/events/export/ai_decisions`
- LLM服务自动记录每轮AI决策数据

### 前端增强  
- ControlPanel增加AI决策导出按钮和说明
- PromptPanel增加单Agent导出功能
- 用户友好的提示信息和错误处理

## 使用场景

1. **AI行为研究**：分析AI在不同情境下的决策模式
2. **Prompt工程优化**：研究不同prompt对AI行为的影响
3. **Thinking过程分析**：了解AI的推理链和思考模式
4. **会话分析**：比较不同实验会话中的AI表现
5. **个体Agent研究**：深入分析特定Agent的行为特征

## 数据过滤

所有导出功能都支持：
- **会话过滤**：选择特定实验会话
- **Agent过滤**：导出特定Agent的数据  
- **时间过滤**：按天过滤数据
- **事件类型过滤**：专门导出AI决策事件

## 注意事项

- AI决策数据仅在实验运行过程中生成
- 导出的CSV文件可能较大，包含完整prompt内容
- 建议使用专业的数据分析工具(如Python pandas)处理大型数据集
- 每个AI决策都包含完整的上下文信息，便于研究分析

通过这些功能，研究人员可以全面了解AI agent的决策过程，为AI行为研究提供宝贵的数据支持。