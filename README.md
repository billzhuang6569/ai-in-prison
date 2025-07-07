# Project Prometheus (普罗米修斯计划)

## AI Social Behavior Simulation Platform

Project Prometheus is an experimental platform that simulates AI agents in controlled social environments. The first scenario recreates the Stanford Prison Experiment to observe emergent AI behaviors, power dynamics, and social relationships.

## 🎯 Features

- **Real-time AI Simulation**: Watch AI agents interact in a virtual prison environment
- **LLM-Powered Decision Making**: Agents use large language models for autonomous decision-making
- **Interactive Monitoring**: Real-time map visualization and agent status monitoring
- **Social Dynamics**: Complex relationship and objective systems
- **WebSocket Communication**: Live updates between backend simulation and frontend interface

## 🏗️ Architecture

- **Backend**: Python + FastAPI + WebSocket for real-time simulation
- **Frontend**: React + Zustand for state management
- **AI Integration**: OpenRouter API for multi-LLM access
- **Communication**: WebSocket for real-time updates + REST API for controls

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 16+ and npm
- OpenRouter API key (optional, will fall back to random actions)

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenRouter API key (optional)
# OPENROUTER_API_KEY=your_key_here
```

### 2. Start Backend Server

```bash
# Option A: Use startup script (recommended)
python start_backend.py

# Option B: Manual start
pip install -r requirements.txt
python main.py
```

The backend will be available at:
- Main API: http://localhost:8000
- WebSocket: ws://localhost:8000/ws
- API Documentation: http://localhost:8000/docs

### 3. Start Frontend (New Terminal)

```bash
# Option A: Use startup script (recommended)
python start_frontend.py

# Option B: Manual start
cd frontend
npm install
npm start
```

The frontend will be available at: http://localhost:3000

### 4. Run Experiment

1. Open http://localhost:3000 in your browser
2. Click "Start Experiment" to begin the simulation
3. Watch AI agents interact in real-time
4. Click on agents to view detailed information
5. Use "Stop Experiment" to pause the simulation

## 🎮 How to Use

### Experiment Controls
- **Start Experiment**: Initialize world and begin AI simulation
- **Stop Experiment**: Pause the simulation
- **Agent Selection**: Click agents on the map to view details

### Interface Layout
- **Left Panel**: Global controls, agent overview, and event log
- **Center Panel**: Interactive prison map with real-time agent positions
- **Right Panel**: Detailed information for selected agents

### Agent Information
Each agent displays:
- Health, sanity, hunger, thirst, and strength levels
- Personality traits (aggression, empathy, logic, obedience, resilience)
- Current inventory and status tags
- Relationships with other agents
- Recent memory and objectives

## 🧠 AI Agent Behavior

### Decision Making
- Agents use LLM prompts that include their personality, status, relationships, and objectives
- If LLM is unavailable, agents fall back to random action selection
- Actions include: move, speak, attack, use items, or rest

### Personality System
- **Aggression**: Tendency toward conflict
- **Empathy**: Concern for others
- **Logic**: Rational decision-making
- **Obedience**: Following rules and authority
- **Resilience**: Mental fortitude

### Status Effects
- **Health**: Physical condition affecting action points
- **Sanity**: Mental state affecting behavior
- **Hunger/Thirst**: Basic needs requiring attention
- **Status Tags**: Visual indicators (hungry, injured, unstable, etc.)

## 🔧 Configuration

### Game Rules
Edit `configs/game_rules.json` to modify:
- Status degradation rates
- Combat damage formulas
- Relationship change rules
- Initial setup parameters

### LLM Models
Configure in `.env`:
- `DEFAULT_MODEL`: Choose from OpenRouter's available models
- `OPENROUTER_API_KEY`: Your API key for LLM access

## 📊 Monitoring

### Event Log
- Real-time stream of all agent actions
- Color-coded by action type (system, action, combat)
- Shows both LLM-driven and random actions

### Agent Analytics
- Live status visualization with progress bars
- Relationship matrices showing social dynamics
- Memory systems tracking agent experiences

## 🛠️ Development

### Project Structure
```
/
├── main.py              # FastAPI application entry
├── requirements.txt     # Python dependencies
├── configs/            # Game configuration files
├── core/               # Simulation engine
├── models/             # Data models and actions
├── services/           # External services (LLM)
├── api/                # WebSocket and REST endpoints
└── frontend/           # React application
```

### Extending the System
- Add new actions in `models/actions.py`
- Modify AI prompts in `services/llm_service.py`
- Create new map layouts in `core/world.py`
- Add UI components in `frontend/src/components/`

## 🔬 Research Applications

This platform is designed for studying:
- AI agent social behavior patterns
- Emergent group dynamics in constrained environments
- Effectiveness of different LLM models for social simulation
- Human-AI interaction parallels in social psychology experiments

## ⚠️ Ethical Considerations

This simulation is designed for research and educational purposes. The prison scenario is used as a controlled environment to study social dynamics, not to glorify or trivialize real prison conditions or human suffering.

## 📝 License

This project is for research and educational use. Please ensure responsible use of AI simulation technologies.

## 🤝 Contributing

This is an experimental research platform. Contributions, suggestions, and research collaborations are welcome.

## 🐛 Troubleshooting

### Common Issues

1. **Backend won't start**: Check Python version (3.10+) and install requirements
2. **Frontend won't start**: Ensure Node.js 16+ and npm are installed
3. **No AI behavior**: Verify OpenRouter API key in .env file
4. **WebSocket connection failed**: Ensure backend is running on port 8000

### Logs and Debugging
- Backend logs appear in terminal running `start_backend.py`
- Frontend logs available in browser developer console
- WebSocket connection status shown in bottom status bar