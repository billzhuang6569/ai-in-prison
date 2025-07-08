# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Project Prometheus (普罗米修斯计划)** - an AI social behavior simulation platform designed to model AI agents in controlled social environments. The first experiment scenario simulates the Stanford Prison Experiment to observe emergent AI behaviors, power dynamics, and social relationships.

**Current Status**: FULLY IMPLEMENTED AND OPTIMIZED. Complete AI simulation platform with advanced UI, real-time trajectory tracking, multi-model LLM integration, and production-ready features.

## Architecture Design

The system is designed with a **frontend-backend separation** architecture:

### Backend (Python)
- **Framework**: FastAPI with asyncio for high-performance async operations
- **Core Architecture**: Modular, object-oriented design
- **Key Components**:
  - `core/engine.py`: Main game loop driving simulation turns
  - `core/world.py`: World state management (singleton pattern)
  - `core/session_manager.py`: Experiment session lifecycle management
  - `models/schemas.py`: Pydantic data models (Agent, WorldState, etc.)
  - `models/actions.py`: Complete action system with session logging
  - `services/llm_service_enhanced.py`: Advanced OpenRouter integration with tool calling
  - `api/websockets.py`: Real-time communication with frontend
  - `api/rest.py`: REST API endpoints with session support
  - `database/event_logger.py`: SQLite event logging with session isolation
  - `configs/game_rules.json`: Configurable game mechanics and rules

### Frontend (React)
- **Framework**: React with component-based architecture
- **State Management**: Zustand store with WebSocket integration
- **Advanced UI Layout**: Grid-based responsive interface (OPTIMIZED)
  - **Left Top**: Experiment controls with Agent configuration modal
  - **Left Bottom**: Event timeline table with data export functionality
  - **Left Sidebar**: Agent preview with recent actions
  - **Center**: Enhanced map with SVG trajectory tracking and real-time synchronization
  - **Right Top**: Interactive agent cards with multiple view modes
  - **Right Bottom**: Detailed agent inspection (thinking, prompts, memory, stats)

### Communication
- **WebSocket**: Real-time world state broadcasting from backend to frontend
- **REST API**: User intervention commands and experiment controls

## Key Design Patterns

### Game Loop Architecture
1. **Environment Update**: Time progression and status updates
2. **Agent Polling**: Sequential activation of AI agents
3. **LLM Integration**: Prompt construction → LLM call → Action parsing → World update
4. **State Broadcasting**: WebSocket push of complete world state

### Data Models
- **Agent**: Comprehensive AI entities with personality traits, status values, relationships, and objectives
- **World**: Singleton state container managing all entities and game state
- **Actions**: Tool-calling system for AI behaviors (move, attack, speak, etc.)
- **Relationships**: N×N matrix tracking inter-agent social dynamics

### LLM Integration
- **OpenRouter**: Multi-model LLM access via API with model selection
- **Model Support**: Claude 3 (Haiku/Sonnet/Opus), GPT-4o, Llama 3.1, Gemini Pro
- **Tool Calling**: Structured JSON responses for AI actions
- **Prompt Engineering**: Revolutionary Guard directive system with hierarchical authority
- **Advanced Prompting**: SESSION-based context with real-time threat detection

## Development Commands

**Current Status**: Full implementation with working build system.

### Backend
- `source venv/bin/activate` - Activate Python virtual environment
- `pip install -r requirements.txt` - Install dependencies
- `python main.py` - Start FastAPI server on http://localhost:24861

### Frontend
- `npm install` - Install Node.js dependencies
- `npm start` - Start React development server on http://localhost:24682

### Full System
- Backend and frontend run concurrently for complete functionality
- WebSocket connection provides real-time state synchronization

## Technical Specifications

### Core Systems
- **Status System**: HP, Sanity, Hunger, Thirst, Strength (0-100 scales)
- **Action Points**: 3 per turn, consumed by different actions
- **Relationship Matrix**: 0-100 scores with contextual descriptions
- **Event System**: Complete logging with SQLite persistence and session isolation
- **Objective System**: Role-based, individual, secret, and emergent goals
- **Session Management**: Unique session IDs for experiment isolation and data integrity

### Map & Environment
- **Grid Size**: 9×16 cells with CSS Grid layout
- **Cell Types**: Cell_Block, Cafeteria, Yard, Solitary, Guard_Room
- **Time System**: Day/Hour progression with status degradation
- **Trajectory Tracking**: SVG-based movement visualization with direction arrows
- **Real-time Sync**: Agent positions and trajectory endpoints perfectly synchronized

### AI Behavior Framework
- **Roles**: Guard, Prisoner with different capabilities and objectives
- **Personality Traits**: Aggression, Empathy, Logic, Obedience, Resilience (0-100)
- **Memory System**: Core and episodic memory affecting decision-making
- **Action Set**: do_nothing, move, use_item, speak, attack (fully implemented with session logging)

## Security Considerations

**Important**: This project involves AI behavioral simulation that could potentially model harmful scenarios. When implementing:
- Ensure all LLM integrations include appropriate safety filters
- Implement safeguards against generating harmful content
- Monitor AI behaviors for concerning patterns
- Maintain clear boundaries between simulation and reality

## Implementation Status

✅ **COMPLETED**: All development phases finished successfully:
1. **Backend Core**: FastAPI setup + complete data models + full game loop with LLM
2. **Frontend Complete**: React setup + WebSocket client + full map visualization + timeline interface
3. **LLM Integration**: Advanced OpenRouter service + comprehensive prompt engineering + action parsing
4. **Full Features**: Complete UI + session management + intervention system + SQLite persistence
5. **Session Management**: Unique experiment sessions with data isolation
6. **UI/UX Optimization**: Grid-based layout + trajectory tracking + model selection
7. **Advanced Features**: Agent configuration modal + data export + real-time synchronization
8. **Bug Fixes**: Attack distance calculation + conversation transmission + ResizeObserver errors

## Latest Enhancements (v2.0)

### 🎯 **Advanced Experiment Controls**
- **Agent Configuration Modal**: Custom Guard/Prisoner counts (1-10 Guards, 1-20 Prisoners)
- **Model Selection**: Support for 7 different LLM models with cost indicators
- **Session Management**: Create new experiments vs continue existing sessions
- **Environment Injection**: Real-time context injection during experiments

### 🗺️ **Enhanced Map Visualization**
- **SVG Trajectory Lines**: Connected movement paths with direction arrows
- **Real-time Synchronization**: Trajectory endpoints perfectly aligned with agent positions
- **Interactive Elements**: Click agents to select across all panels
- **Visual Indicators**: Start/end markers, trajectory toggle, improved agent labels (G1, P1, P2...)

### 🎴 **Comprehensive Agent Management**
- **Agent Cards**: Overview, personality, relationships, inventory view modes
- **Agent Details**: Thinking process, complete prompts, memory system, detailed stats
- **Agent Preview**: Recent actions, health status, real-time updates
- **Cross-panel Selection**: Synchronized selection across map, cards, and details

### 📊 **Data Analysis & Export**
- **Timeline Events**: Comprehensive event table with agent-specific filtering
- **Export Capabilities**: CSV, JSON, and session summary downloads
- **Session Analytics**: Event statistics, interaction tracking, behavior analysis
- **Time-based Filtering**: Day/hour/minute level event organization

## Current Running Servers
- **Backend**: http://localhost:24861 (FastAPI + WebSocket)
- **Frontend**: http://localhost:24682 (React development server)
- **Status**: Production ready with advanced features for comprehensive AI behavioral research

## Key Components Created

### Frontend Components
- `ExperimentControl.js` - Advanced experiment controls with model selection and agent configuration
- `EventTable.js` - Timeline event visualization with data export capabilities
- `AgentPreview.js` - Real-time agent overview with recent actions
- `AgentCards.js` - Interactive agent cards with multiple view modes
- `AgentDetails.js` - Comprehensive agent inspection (thinking, prompts, memory, stats)
- `MapView.js` - Enhanced map with SVG trajectory tracking and real-time synchronization

### Backend Enhancements
- Guard prompt optimization with hierarchical directive system
- Attack distance calculation fixes (Manhattan vs Chebyshev)
- Session management and data export endpoints
- Model selection parameter support

For detailed development progress, see CLAUDE_PLAN.md