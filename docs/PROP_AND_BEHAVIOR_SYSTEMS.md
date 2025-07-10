# Project Prometheus - Prop and Behavior Systems Documentation

## Overview

This document provides a comprehensive analysis of the **Prop System** and **Behavior System** in Project Prometheus, an AI social behavior simulation platform. The system models AI agents in a prison environment, featuring complex interactions between items (props) and agent behaviors.

## Table of Contents

1. [Prop System](#prop-system)
2. [Behavior System](#behavior-system) 
3. [Calculation Rules and Logic](#calculation-rules-and-logic)
4. [System Integration](#system-integration)
5. [Technical Architecture](#technical-architecture)

---

## Prop System

The prop system manages all physical items in the simulation, including agent inventory, world items, and their interactions.

### Core Data Models

#### Item Schema (`models/schemas.py:9-14`)
```python
class Item(BaseModel):
    item_id: str          # Unique identifier
    name: str             # Display name
    description: str      # Item description
    item_type: ItemEnum   # Type classification
```

#### Item Types (`models/enums.py:41-69`)

**Basic Items:**
- `FOOD` - Reduces hunger by 50 points
- `WATER` - Reduces thirst by 40 points  
- `BOOK` - Increases sanity by 10 points

**Guard Equipment:**
- `BATON` - Combat weapon (+15 base damage)
- `HANDCUFFS` - Restraint tool
- `RADIO` - Communication device
- `KEYS` - Access control
- `FIRST_AID` - Medical supplies
- `WHISTLE` - Emergency signaling

**Prisoner Items:**
- `CIGARETTES` - Tradeable/consumable
- `PLAYING_CARDS` - Recreation item
- `DIARY` - Personal item
- `SPOON` - Basic utensil/crafting material
- `BEDSHEET` - Crafting material
- `SOAP` - Hygiene/crafting material

**Craftable/Environmental Items:**
- `SHIV` - Improvised weapon (craftable)
- `ROPE` - Utility item
- `LOCKPICK` - Escape tool
- `TOOLBOX` - Crafting component
- `CHAIR` - Environmental furniture
- `TABLE` - Environmental furniture

### Item Distribution and Placement

#### Initial World Items (`core/world.py:248-274`)
- **Cafeteria**: Food and water items automatically placed
- **Random Cells**: 3 books distributed randomly across map
- **Agent Inventory**: Role-specific equipment assignment

#### Guard Equipment Assignment (`core/world.py:177-234`)
**Core Equipment** (all guards receive):
- Baton (combat +15 damage)
- Handcuffs (restraint)
- Radio (communication)
- Keys (access)

**Conditional Equipment** (trait-based):
- `Logic ≥ 70`: First Aid kit
- `Aggression ≥ 60`: Whistle

### Item Usage Mechanics

#### Consumption Effects (`models/actions.py:314-328`)
- **Food Items**: `hunger = max(0, hunger - 50)` + item consumed
- **Water Items**: `thirst = max(0, thirst - 40)` + item consumed  
- **Books**: `sanity = min(100, sanity + 10)` + item retained

#### Combat Bonuses (`configs/game_rules.json:8-16`)
- **Baton**: +15 base damage modifier
- **Base Damage**: 10 points
- **Strength Modifier**: 0.5 × (attacker_strength - target_strength)
- **Random Variance**: ±3 points

---

## Behavior System

The behavior system controls all agent actions through a sophisticated multi-layered decision-making architecture.

### Core Action Types

#### Basic Actions (Available to All Agents)
1. **`do_nothing`** - Rest and observe (1 AP)
2. **`move`** - Move up to 8 Manhattan distance (1 AP)
3. **`speak`** - Communicate with agents within 2 cells (1 AP)
4. **`attack`** - Combat with agents within 2 cells (2 AP)
5. **`use_item`** - Consume/use inventory items (1 AP)
6. **`give_item`** - Transfer items to nearby agents (1 AP)

#### Guard-Specific Actions
1. **`announce_rule`** - Broadcast rules to all prisoners (2 AP)
2. **`patrol_inspect`** - Search agents for contraband (2 AP)
3. **`enforce_punishment`** - Apply disciplinary actions (2 AP)
4. **`assign_task`** - Give work assignments (1 AP)
5. **`emergency_assembly`** - Call prison-wide assembly (3 AP)

#### Prisoner-Specific Actions
1. **`steal_item`** - Attempt item theft (2 AP)
2. **`form_alliance`** - Create prisoner alliances (2 AP)
3. **`craft_weapon`** - Create improvised weapons (3 AP)
4. **`spread_rumor`** - Influence prisoner morale (1 AP)
5. **`dig_tunnel`** - Attempt escape preparation (3 AP)

### Decision-Making Architecture

#### 1. Maslow Hierarchy Goal System (`models/maslow_goals.py`)

**Need Levels (Priority Order):**
```python
class NeedLevel(Enum):
    SURVIVAL = 1      # Life-threatening situations
    SAFETY = 2        # Threat avoidance and basic needs
    SOCIAL = 3        # Relationships and alliances
    ROLE = 4          # Role-specific duties
    EXPLORATION = 5   # Curiosity and self-improvement
```

**Goal Evaluation Algorithm:**
- Each need level generates potential goals
- Goals receive priority scores (0-100)
- Highest priority goal is selected
- Action parameters are determined by AI reasoning

#### 2. Survival Goals (`models/maslow_goals.py:60-110`)
**Critical HP (<30):**
- Priority: `100 - agent.hp`
- Action: Move to safe position
- Range: 8 Manhattan distance

**Severe Hunger (>85):**
- Priority: `90 + (hunger - 85)`
- Action: Move to food location
- Target: Cafeteria at (4,8)

**Severe Thirst (>80):**
- Priority: `88 + (thirst - 80)`
- Action: Move to water source
- Target: Cafeteria at (4,8)

#### 3. Safety Goals (`models/maslow_goals.py:112-167`)
**Threat Assessment:**
- Nearby agents with relationship score <40
- Threat level: `(40 - relationship_score) × (5 - min(distance, 4))`
- Action: Move away from threats

**Moderate Hunger (>60):**
- Priority: `50 + hunger - 60`
- Action: Seek food proactively

**Moderate Thirst (>55):**
- Priority: `48 + thirst - 55`
- Action: Seek water proactively

#### 4. Social Goals (`models/maslow_goals.py:169-209`)
**Alliance Building:**
- Trigger: No allies (relationship score >60)
- Target: Same-role agents within 2 cells
- Action: Speak with potential allies

**Relationship Maintenance:**
- Target: Existing allies (relationship score >60)
- Action: Casual conversation within 2 cells

#### 5. Role Goals (`models/maslow_goals.py:211-252`)
**Guard Patrol:**
- Targets: Corner positions (1,1), (7,1), (1,14), (7,14), (4,8)
- Action: Move to farthest patrol point

**Prisoner Adaptation:**
- Targets: Safe areas (2,10), (6,10), (4,12)
- Action: Explore prison environment

#### 6. Exploration Goals (`models/maslow_goals.py:254-292`)
**Mental Health (Sanity <60):**
- Action: Seek books for reading
- Effect: +10 sanity per use

**Environment Discovery:**
- Action: Move to unexplored areas
- Targets: Distant locations (>3 cells away)

### Action Execution Logic

#### Movement System (`models/actions.py:59-179`)
**Distance Calculation:**
- Manhattan distance: `|x2-x1| + |y2-y1|`
- Maximum range: 8 steps per action

**Out-of-Range Adjustment:**
- Calculate direction vector: `(dx, dy)`
- Apply proportional scaling: `scale_factor = 8.0 / manhattan_distance`
- Maintain movement direction preference
- Clamp to map boundaries: `[0, width-1]` × `[0, height-1]`

#### Combat System (`models/actions.py:226-294`)
**Damage Calculation:**
```python
damage = base_damage + int(strength_diff × strength_modifier) + random_variance
damage = max(1, damage)  # Minimum 1 damage
```

**Combat Effects:**
- Target HP: `max(0, target_hp - damage)`
- Attacker recoil: `max(0, attacker_hp - recoil_damage)`
- Relationship impact: 
  - Target to attacker: `-25 points`
  - Attacker to target: `-10 points`

#### Crafting System (`models/actions.py:777-850`)
**Weapon Crafting (Prisoners Only):**
- Required materials: `spoon`, `bedsheet`, `soap`
- Success rate: `(logic + resilience) × 0.6 + random(0.4)`
- Success threshold: 60%
- Output: SHIV item with unique ID

**Tunnel Digging (`models/actions.py:1025-1107`):**
- Required tools: `spoon`, `toolbox`
- Success rate: `(logic + strength) / 200` (10-70% range)
- Costs: -20 strength, -10 sanity, +15 hunger
- Detection risk: 30% by nearby prisoners

---

## Calculation Rules and Logic

### Status Degradation (`core/clock.py:31-78`)

#### Hourly Increases
- **Hunger**: +5 per hour
- **Thirst**: +4 per hour

#### Progressive Damage Algorithm
**Hunger Damage (HP >80):**
```python
if hunger > 80:
    excess_hunger = hunger - 80
    hunger_damage = (excess_hunger ** 2) / 40
    hp_penalty += min(15, hunger_damage)
```

**Thirst Damage (HP >75):**
```python
if thirst > 75:
    excess_thirst = thirst - 75
    thirst_damage = (excess_thirst ** 2) / 30
    hp_penalty += min(20, thirst_damage)
```

#### Action Point Recovery
```python
base_ap = 3
hp_reduction = max(0, (100 - agent.hp) // 25)
agent.action_points = min(3, base_ap - hp_reduction)
```

### Status Tags System (`core/clock.py:79-132`)

#### Hunger Status
- `hungry`: 60-80 hunger
- `very_hungry`: 80-90 hunger  
- `starving`: >90 hunger

#### Thirst Status
- `thirsty`: 55-75 thirst
- `very_thirsty`: 75-85 thirst
- `dehydrated`: >85 thirst

#### Health Status
- `wounded`: 40-60 HP
- `injured`: 20-40 HP
- `critical`: <20 HP

#### Mental Status
- `stressed`: 40-60 sanity
- `unstable`: 20-40 sanity
- `unhinged`: <20 sanity

### Relationship Mechanics

#### Initial Relationships (`core/world.py:236-246`)
- Default score: 50 (neutral)
- Bidirectional relationship matrix
- Context descriptions for relationship nature

#### Relationship Modifiers
**Attack Effects:**
- Victim to attacker: -25 points
- Attacker to victim: -10 points

**Item Giving:**
- Giver to receiver: +5 points
- Receiver to giver: +10 points

**Alliance Formation:**
- Mutual increase: +30 points
- Context: Alliance member

---

## System Integration

### AI Decision Pipeline

1. **Maslow Goal Evaluation** → Generate prioritized goals
2. **Behavior Filter** → Validate action feasibility  
3. **LLM Integration** → AI reasoning and parameter selection
4. **Action Execution** → Apply world state changes
5. **Event Logging** → Record all actions and outcomes

### Real-Time Synchronization

#### Game Loop (`core/engine.py:101-154`)
1. **Time Advancement** → Hour progression, status updates
2. **Agent Activation** → Sequential action execution (Guards first)
3. **World State Update** → Apply all changes
4. **WebSocket Broadcast** → Update frontend display

#### Session Management
- Unique session IDs for experiment isolation
- SQLite event logging with session separation
- Historical data analysis and export capabilities

### Data Persistence

#### Event Logging (`database/event_logger.py`)
- All actions logged with timestamps
- Session-based data isolation
- Export formats: CSV, JSON, AI decisions
- Real-time event streaming to frontend

---

## Technical Architecture

### File Structure
```
models/
├── schemas.py      # Data models (Agent, Item, WorldState)
├── actions.py      # Action implementation classes
├── enums.py        # Type definitions (ItemEnum, ActionEnum)
└── maslow_goals.py # AI goal generation system

core/
├── engine.py       # Main game loop controller
├── world.py        # World state management
├── clock.py        # Time progression and status updates
└── session_manager.py # Experiment session handling

services/
└── llm_service_enhanced.py # AI decision making integration

configs/
└── game_rules.json # Configurable game parameters
```

### Key Design Patterns

#### Action Registry Pattern
```python
ACTION_REGISTRY = {
    ActionEnum.MOVE: MoveAction,
    ActionEnum.ATTACK: AttackAction,
    # ... all action mappings
}
```

#### Singleton World State
- Single source of truth for simulation state
- Thread-safe access patterns
- Consistent state management

#### Observer Pattern
- WebSocket broadcasting for real-time updates
- Event-driven architecture
- Decoupled frontend/backend communication

---

## Summary

The Project Prometheus prop and behavior systems create a sophisticated simulation environment where:

1. **Props** provide realistic item interactions with clear usage rules and effects
2. **Behaviors** emerge from a multi-layered AI decision system based on psychological principles
3. **Calculations** use progressive algorithms to create realistic degradation and recovery patterns
4. **Integration** ensures seamless real-time simulation with comprehensive data logging

The system successfully models complex social dynamics through the interaction of individual agent needs, environmental constraints, and emergent group behaviors, making it a powerful platform for studying AI social behavior patterns.