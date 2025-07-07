# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Project Prometheus (普罗米修斯计划)** - an AI social behavior simulation platform designed to model AI agents in controlled social environments. The first experiment scenario simulates the Stanford Prison Experiment to observe emergent AI behaviors, power dynamics, and social relationships.

**Current Status**: Documentation-only phase. No implementation code exists yet.

## Architecture Design

The system is designed with a **frontend-backend separation** architecture:

### Backend (Python)
- **Framework**: FastAPI with asyncio for high-performance async operations
- **Core Architecture**: Modular, object-oriented design
- **Key Components**:
  - `core/engine.py`: Main game loop driving simulation turns
  - `core/world.py`: World state management (singleton pattern)
  - `models/agent.py`: AI agent entities with personality, status, relationships
  - `services/llm_service.py`: OpenRouter integration for LLM decision-making
  - `api/websockets.py`: Real-time communication with frontend
  - `configs/game_rules.json`: Configurable game mechanics and rules

### Frontend (React)
- **Framework**: React with component-based architecture
- **State Management**: Zustand or Redux Toolkit recommended
- **Layout**: Three-column interface
  - Left: Global monitoring and controls
  - Center: 9x16 prison map visualization
  - Right: Individual agent details and intervention tools

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
- **OpenRouter**: Multi-model LLM access via API
- **Tool Calling**: Structured JSON responses for AI actions
- **Prompt Engineering**: Comprehensive context including personality, status, relationships, and objectives

## Development Commands

**Note**: No build system is currently implemented. When code is added, typical Python commands would be:
- `pip install -r requirements.txt` - Install dependencies
- `python main.py` - Start FastAPI server
- `pytest` - Run tests (when implemented)
- `ruff check` - Lint code (when implemented)

## Technical Specifications

### Core Systems
- **Status System**: HP, Sanity, Hunger, Thirst, Strength (0-100 scales)
- **Action Points**: 3 per turn, consumed by different actions
- **Relationship Matrix**: 0-100 scores with contextual descriptions
- **Event System**: Automatic and choice-driven events affecting world state
- **Objective System**: Role-based, individual, secret, and emergent goals

### Map & Environment
- **Grid Size**: 9×16 cells
- **Cell Types**: Cell_Block, Cafeteria, Yard, Solitary, Guard_Room
- **Time System**: Day/Hour progression with status degradation

### AI Behavior Framework
- **Roles**: Guard, Prisoner with different capabilities and objectives
- **Personality Traits**: Aggression, Empathy, Logic, Obedience, Resilience (0-100)
- **Memory System**: Core and episodic memory affecting decision-making
- **Action Set**: do_nothing, move, pickup_item, use_item, speak, attack, report_to_warden

## Security Considerations

**Important**: This project involves AI behavioral simulation that could potentially model harmful scenarios. When implementing:
- Ensure all LLM integrations include appropriate safety filters
- Implement safeguards against generating harmful content
- Monitor AI behaviors for concerning patterns
- Maintain clear boundaries between simulation and reality

## Future Implementation Notes

When beginning implementation, follow this development roadmap:
1. **Backend Core**: FastAPI setup + basic data models + game loop without LLM
2. **Frontend Basic**: React setup + WebSocket client + basic map visualization  
3. **LLM Integration**: OpenRouter service + prompt engineering + action parsing
4. **Full Features**: Complete UI + analytics + intervention system + persistence