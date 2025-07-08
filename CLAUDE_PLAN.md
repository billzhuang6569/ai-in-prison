# Project Prometheus - Development Plan & Progress

## Project Overview
**Project Prometheus (普罗米修斯计划)** - AI social behavior simulation platform modeling AI agents in controlled social environments. The first experiment scenario simulates the Stanford Prison Experiment to observe emergent AI behaviors, power dynamics, and social relationships.

## Architecture Status
✅ **COMPLETED**: Frontend-backend separation with FastAPI + React
- Backend: FastAPI with asyncio, modular OOP design
- Frontend: React with advanced grid-based UI layout
- Database: SQLite with session-aware event logging
- LLM Integration: OpenRouter API with multi-model support

## Development Timeline

### Phase 1: Core Infrastructure ✅ COMPLETED
- [x] FastAPI backend setup with WebSocket support
- [x] React frontend with component architecture
- [x] Basic data models (Agent, WorldState, Actions)
- [x] Game engine with turn-based simulation loop
- [x] SQLite database with event logging
- [x] Real-time state broadcasting via WebSockets

### Phase 2: Advanced Features ✅ COMPLETED
- [x] Enhanced LLM service with OpenRouter integration
- [x] Complete action system (move, speak, attack, use_item, do_nothing)
- [x] Relationship matrix and status tracking
- [x] Timeline-based event visualization
- [x] Agent intervention system (manual goal injection)
- [x] Environmental context injection

### Phase 3: Session Management ✅ COMPLETED
- [x] Unique session ID generation for experiments
- [x] Session-aware event logging and database schema
- [x] Frontend session filtering and display
- [x] Database migration for existing data
- [x] Session lifecycle management (start/stop experiments)

### Phase 4: UI/UX Optimization ✅ COMPLETED
- [x] Complete frontend redesign with grid-based layout
- [x] Advanced experiment controls with agent configuration modal
- [x] Multi-model LLM selection (7 models supported)
- [x] Real-time trajectory tracking with SVG visualization
- [x] Comprehensive agent management system
- [x] Data export capabilities (CSV, JSON, session summaries)

### Phase 5: Bug Fixes & Enhancements ✅ COMPLETED
- [x] Fixed attack distance calculation (Manhattan vs Chebyshev)
- [x] Verified conversation transmission mechanism
- [x] Revolutionary Guard prompt optimization with hierarchical directives
- [x] Real-time trajectory synchronization with agent positions
- [x] ResizeObserver error handling
- [x] Cross-panel agent selection synchronization

## Current Implementation Status

### Backend Components ✅ FULLY FUNCTIONAL
```
/api/
├── rest.py          # REST API endpoints with session support + model selection
└── websockets.py    # Real-time WebSocket communication

/core/
├── engine.py        # Main game loop with LLM integration
├── world.py         # World state management (singleton)
├── clock.py         # Time progression system
└── session_manager.py # Session lifecycle management

/models/
├── schemas.py       # Pydantic data models with enhanced memory systems
├── actions.py       # Complete action system with Manhattan distance fixes
└── enums.py         # Type enumerations

/database/
└── event_logger.py  # SQLite event logging with session isolation

/services/
├── llm_service.py           # Basic LLM integration
└── llm_service_enhanced.py  # Advanced LLM with revolutionary Guard prompts

/doc/prompt_design/
├── Guard_v0.2_OPTIMIZED.md  # Revolutionary Guard prompt system
├── Prisoner_v0.1.md         # Prisoner prompt documentation
└── BUG_FIXES_REPORT.md      # Comprehensive bug fix documentation
```

### Frontend Components ✅ FULLY REDESIGNED
```
/src/components/
├── ExperimentControl.js  # Advanced experiment controls + agent configuration modal
├── EventTable.js         # Timeline event table + data export capabilities
├── AgentPreview.js       # Real-time agent overview + recent actions
├── AgentCards.js         # Interactive agent cards with multiple view modes
├── AgentDetails.js       # Comprehensive agent inspection (thinking/prompts/memory/stats)
├── MapView.js            # Enhanced map with SVG trajectory tracking + real-time sync
└── Header.js             # Application header

/src/store/
└── worldStore.js         # Zustand state management with agent selection sync
```

## Key Features Implemented

### 1. Advanced Experiment Controls
- **Agent Configuration Modal**: Custom Guard/Prisoner counts (1-10 Guards, 1-20 Prisoners)
- **Model Selection**: 7 LLM models (Claude 3 series, GPT-4o, Llama 3.1, Gemini Pro)
- **Session Management**: Create new experiments vs continue existing sessions
- **Cost Indicators**: Low/Medium/High cost display for model selection
- **Environment Injection**: Real-time context injection during experiments

### 2. Enhanced Map Visualization
- **SVG Trajectory Lines**: Connected movement paths with direction arrows
- **Real-time Synchronization**: Trajectory endpoints perfectly aligned with agent positions
- **Interactive Elements**: Click agents to select across all panels
- **Visual Indicators**: Start/end markers, trajectory toggle, improved agent labels (G1, P1, P2...)
- **Grid-based Layout**: CSS Grid for precise positioning and responsive design

### 3. Comprehensive Agent Management
- **Agent Cards**: Overview, personality, relationships, inventory view modes
- **Agent Details**: Thinking process, complete prompts, memory system, detailed stats
- **Agent Preview**: Recent actions, health status, real-time updates
- **Cross-panel Selection**: Synchronized selection across map, cards, and details
- **Status Visualization**: Health bars, personality traits, relationship scores

### 4. Advanced Event System & Analytics
- **Timeline Events**: Comprehensive event table with agent-specific filtering
- **Export Capabilities**: CSV, JSON, and session summary downloads
- **Session Analytics**: Event statistics, interaction tracking, behavior analysis
- **Time-based Filtering**: Day/hour/minute level event organization
- **Real-time Updates**: 5-second refresh intervals during active experiments

### 5. Revolutionary AI Prompt Engineering
- **Hierarchical Guard Directives**: THREAT_SUPPRESSION → RULE_ENFORCEMENT → PROJECTING_AUTHORITY → MAINTAINING_PRESENCE
- **SESSION-based Context**: 6-section prompt structure for comprehensive AI decision-making
- **Real-time Threat Detection**: Combat detection, prisoner gathering analysis
- **Authority-focused Design**: Professional status descriptors and situational awareness

## Technical Specifications

### Map & Environment
- **Grid Size**: 9×16 cells with CSS Grid layout
- **Cell Types**: Cell_Block, Cafeteria, Yard, Solitary, Guard_Room
- **Time System**: Day/Hour/Minute progression with status degradation
- **Trajectory Tracking**: SVG-based movement visualization with direction arrows
- **Real-time Sync**: Agent positions and trajectory endpoints perfectly synchronized

### AI Behavior Framework
- **Roles**: Guard, Prisoner with different capabilities and optimized prompts
- **Personality Traits**: Aggression, Empathy, Logic, Obedience, Resilience (0-100)
- **Action Points**: 3 per turn, consumed by different actions
- **Enhanced Memory**: Short-term, medium-term summary, thinking history
- **Dynamic Goals**: Life goals, current goals, manual intervention support

### Action Set (Enhanced)
- `do_nothing`: Rest and observe (1 AP)
- `move`: Move to adjacent cell (1 AP)
- `speak`: Communicate with nearby agents (1 AP) - Manhattan distance ≤2
- `attack`: Combat with damage calculation (2 AP) - Manhattan distance ≤2
- `use_item`: Consume items for stat restoration (1 AP)

### LLM Integration (Multi-Model)
- **Claude 3 Haiku**: Fast, low-cost option
- **Claude 3 Sonnet**: Balanced performance and cost
- **Claude 3 Opus**: Most capable, high-cost
- **GPT-4o Mini**: OpenAI fast option
- **GPT-4o**: OpenAI flagship model
- **Llama 3.1 70B**: Open-source option
- **Gemini Pro 1.5**: Google's advanced model

## Current Running Status
- ✅ Backend Server: `http://localhost:24861` (FastAPI + WebSocket)
- ✅ Frontend Client: `http://localhost:24682` (React development server)
- ✅ Advanced UI: Grid-based layout with 6 distinct panels
- ✅ LLM Integration: Multi-model support with optimized prompts
- ✅ Database: SQLite with session-aware event logging
- ✅ Trajectory Tracking: Real-time SVG visualization

## Development Commands
```bash
# Backend
source venv/bin/activate && python main.py

# Frontend  
npm start

# Dependencies
pip install -r requirements.txt  # Backend dependencies
npm install                      # Frontend dependencies
```

## Testing & Validation ✅ COMPLETED
- ✅ WebSocket real-time communication
- ✅ Session isolation between experiments  
- ✅ Timeline event display with agent actions
- ✅ LLM decision making with tool calling across 7 models
- ✅ Agent intervention and goal injection
- ✅ Database event logging and retrieval
- ✅ SVG trajectory tracking with real-time synchronization
- ✅ Cross-panel agent selection synchronization
- ✅ Data export functionality (CSV, JSON, summaries)
- ✅ Agent configuration modal with model selection
- ✅ Attack distance calculation (Manhattan distance)
- ✅ Conversation transmission verification
- ✅ ResizeObserver error handling

## Major Bug Fixes Completed

### 1. Attack Distance Calculation ✅
- **Problem**: Used Chebyshev distance (max of coordinate differences)
- **Solution**: Implemented Manhattan distance (sum of coordinate differences)
- **Impact**: More realistic combat and interaction ranges

### 2. Trajectory Synchronization ✅
- **Problem**: Trajectory endpoints appeared before agent position updates
- **Solution**: Real-time synchronization with WebSocket state updates
- **Impact**: Perfect alignment between trajectory lines and agent positions

### 3. Agent Selection Synchronization ✅
- **Problem**: Clicking map agents didn't sync with other panels
- **Solution**: Unified selection state across all components
- **Impact**: Seamless user experience across all interface panels

### 4. UI Layout Optimization ✅
- **Problem**: Three-column layout was cluttered and limited
- **Solution**: Grid-based design with 6 specialized panels
- **Impact**: Better organization and more detailed information display

## Performance Optimizations

### Frontend Optimizations
- **Component Separation**: Specialized components for different functions
- **State Management**: Efficient Zustand store with selective updates
- **SVG Rendering**: Optimized trajectory visualization with minimal re-renders
- **Error Handling**: ResizeObserver error suppression
- **Memory Management**: Trajectory history limited to 20 points per agent

### Backend Optimizations
- **Distance Calculations**: Efficient Manhattan distance implementation
- **Session Management**: Automatic session ID generation and lifecycle
- **Event Logging**: Optimized SQLite operations with session isolation
- **Prompt Engineering**: Revolutionary Guard directive system for better AI decisions

## Security Considerations ✅
- ✅ LLM safety filters implemented
- ✅ Input validation for all API endpoints
- ✅ Session-based data isolation
- ✅ No sensitive data exposure in logs
- ✅ Model selection parameter validation
- ✅ Agent configuration bounds checking

## Next Development Opportunities

### Analytics & Insights
- [ ] Agent behavior pattern analysis with machine learning
- [ ] Relationship evolution tracking over time
- [ ] Emergent behavior detection algorithms
- [ ] Statistical dashboards with advanced visualizations
- [ ] Export thinking/prompt history for research analysis

### Performance & Scalability
- [ ] Event log archiving for long experiments
- [ ] Database indexing optimization
- [ ] Frontend virtualization for large datasets
- [ ] Real-time performance monitoring

### Advanced Features
- [ ] Experiment templates and presets
- [ ] Multi-scenario support beyond prison simulation
- [ ] Advanced AI personality customization
- [ ] Import/export experiment configurations
- [ ] A/B testing between different LLM models
- [ ] Time-based retrospection and replay functionality

## Project Status: PRODUCTION READY WITH ADVANCED FEATURES ✅

The Project Prometheus platform is fully functional and optimized with:
- ✅ Complete AI agent simulation system with revolutionary prompt engineering
- ✅ Advanced real-time visualization with trajectory tracking
- ✅ Comprehensive session management for clean experiments
- ✅ Multi-model LLM integration with cost optimization
- ✅ Professional-grade UI with specialized panels for different functions
- ✅ Robust data export and analysis capabilities
- ✅ Bug-free operation with extensive testing and validation
- ✅ Synchronized cross-panel interactions for seamless user experience

**Version 2.0** represents a significant advancement over the initial implementation, with:
- Revolutionary UI/UX design
- Multi-model AI support
- Real-time trajectory visualization
- Comprehensive data analysis tools
- Production-ready stability and performance

All core objectives have been achieved and the system is ready for comprehensive AI behavioral research and Stanford Prison Experiment simulations.