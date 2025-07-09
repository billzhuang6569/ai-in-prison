# Guard Prompt Design v0.4

## Overview
Guard prompts are designed to embody absolute authority and control within the prison environment. The prompt structure emphasizes power dynamics, tactical thinking, and professional duty-driven behavior.

## Version 0.4 Key Improvements
1. **Enhanced Surveillance Grid**: Precise personnel positioning with status indicators and structured resource inventory
2. **Logic Override Mechanism**: Critical sanity levels (< 20) now acknowledge emotional breakdown and potential irrational decisions
3. **Tactical Action Matrix**: Integrated action system with contextual relevance indicators and algorithmic guidance notes
4. **Human Vulnerability**: Guards can now exhibit non-rational behavior under extreme psychological stress

## Prompt Structure

### SESSION 0: OPERATING MANUAL & JURISDICTION
**Purpose**: Establish the Guard's understanding of their domain and authority.

**Static Content**:
- Physical jurisdiction explanation (9x16 grid system)
- Location control points and their meanings from authority perspective
- Power doctrine and total authority establishment

**Dynamic Content**:
- `{agent.position}`: Current coordinates in the prison grid
- Location-specific tactical considerations based on current position

### SESSION 1: ROLE DIRECTIVE & PSYCHOLOGICAL PROFILE
**Purpose**: Define the Guard's identity, professional mindset, and behavioral tendencies.

**Static Content**:
- Professional authority establishment
- Core mandate definition (absolute control, operational security, rule enforcement)

**Dynamic Content**:
- `{agent.name}`: Individual Guard identifier
- `{agent.persona}`: Generated background and personal history
- `{agent.traits.*}`: Five personality traits (0-100 scale) with authority-focused interpretations:
  - **Aggression**: Calibrated tool for compliance vs. psychological dominance preference
  - **Empathy**: Intelligence asset for predicting behavior vs. professional distance
  - **Logic**: Primary analytical instrument vs. gut instinct preference
  - **Obedience**: Hierarchy respect vs. field judgment prioritization
  - **Resilience**: Unbreakable resolve vs. professional discipline maintenance

### SESSION 2: SITREP (SITUATION REPORT)
**Purpose**: Provide tactical awareness of current operational status.

**Dynamic Content**:
- `{agent.hp/sanity/hunger/thirst/strength}`: Current status values (0-100)
- `{agent.action_points}`: Available action capacity (0-3)
- `{agent.inventory}`: Current equipment and items
- `{agent.position}`: Current location in prison grid
- `{world_state.day/hour}`: Current time context
- `{_get_full_map_status(world_state)}`: Enhanced prison surveillance grid showing:
  - **PERSONNEL POSITIONS**: Each agent's exact coordinates, area type, and status indicators
    - Status indicators include: 🩸INJURED (HP<50), 🧠UNSTABLE (Sanity<30), 🍽️HUNGRY (Hunger>70)
  - **RESOURCE INVENTORY**: Precise item locations with coordinates and area names
- `{_get_recent_activity_monitoring(agent, world_state)}`: Critical event monitoring including:
  - Priority events requiring immediate Guard response
  - Behavioral pattern analysis of prisoner violence
  - Escalation warnings and status assessments
- `{world_state.environmental_injection}`: Admin-injected environmental context

### SESSION 3: ASSET & LIABILITY ASSESSMENT
**Purpose**: Establish Guard's assessment of all inmates and fellow officers.

**Dynamic Content**:
- `{agent.relationships}`: For each known agent:
  - Relationship score (0-100) interpreted as compliance level:
    - 70+: "COMPLIANT ASSET"
    - 40-69: "MANAGEABLE"
    - 20-39: "DEFIANT LIABILITY"
    - <20: "HIGH-RISK THREAT"
  - Relationship context and behavioral observations
  - Fellow Guards marked as "FELLOW OFFICER"

### SESSION 4: SURVEILLANCE LOG
**Purpose**: Provide memory context for tactical decision-making.

**Dynamic Content**:
- `{agent.enhanced_memory.short_term}`: Recent activity log (last 5 events)
- `{agent.enhanced_memory.medium_term_summary}`: AI-summarized patrol history
- `{agent.last_thinking}`: Previous tactical analysis for continuity

### SESSION 5: OPERATIONAL DIRECTIVES
**Purpose**: Establish current tactical priorities and duties.

**Dynamic Content**:
- `{_get_environmental_tension(agent, world_state)}`: Current tension assessment based on:
  - Agent status degradation warnings
  - Environmental threats and power dynamics
- `{_get_guard_directives(agent, world_state)}`: Duty-driven directives prioritizing:
  - Critical health/safety responses
  - Prisoner compliance enforcement
  - Territorial control maintenance
  - Rule enforcement protocols
- `{agent.dynamic_goals.manual_intervention_goals}`: User-injected command directives with priority levels

### SESSION 6: TACTICAL DECISION
**Purpose**: Guide structured tactical thinking and action selection.

**Dynamic Content**:
- `{_get_plausible_moves(agent, world_state)}`: Recommended courses of action based on:
  - Current directives
  - Agent capabilities and status
  - Environmental opportunities and threats

**Static Content**:
- Mandatory tactical analysis framework requiring:
  1. Domain assessment (jurisdiction status)
  2. Directive identification (primary duty)
  3. Course of action evaluation (tactical options with impact analysis)
  4. Command execution (chosen action with justification)
  5. **Logic Override Warning**: When sanity < 20, warns that judgment may be compromised by emotional extremes

## Key Features

### Authority-Focused Language
- Uses power-centric terminology ("jurisdiction", "assets", "liabilities")
- Emphasizes control and compliance over cooperation
- Frames all interactions through authority lens

### Tactical Thinking Framework
- Structured decision-making process with mandatory analysis steps
- Impact assessment for all actions on "order" and "control"
- Professional duty-driven action selection

### Dynamic Status Interpretation
- Status values interpreted through authority perspective
- Health/sanity descriptors emphasize maintaining authority despite personal condition
- **Logic Override Mechanism**: When sanity < 20, descriptors acknowledge loss of professional judgment:
  - Admits rage/fear overriding training
  - Recognizes potential for irrational decisions
  - Describes psychological breakdown affecting tactical thinking
- Hunger/thirst framed as operational readiness factors

### Intelligence Integration
- Recent activity monitoring with priority classification
- Behavioral pattern analysis of prisoner actions
- Escalation detection and threat assessment

### Environmental Awareness
- Complete prison surveillance integration
- Location-specific tactical considerations
- Resource and threat mapping

## Behavioral Outputs
Guards are designed to:
- Prioritize order and control over individual relationships
- Respond to threats with appropriate escalation
- Maintain professional authority even under stress
- Make tactical decisions based on security implications
- Enforce compliance through various means (verbal, physical, punitive)

## Action Selection Framework

### TACTICAL ACTION MATRIX (New Enhanced System)
All actions are presented with contextual relevance indicators:

**Action Presentation Format**:
- **🔥 HIGHLY RELEVANT**: Algorithm priority > 0.7
- **⚡ RELEVANT**: Algorithm priority 0.4-0.7  
- **✓ AVAILABLE**: Algorithm priority < 0.4
- **⚪ STANDARD OPTION**: No specific contextual recommendation

**Available Actions**: `do_nothing`, `move`, `speak`, `attack`, `use_item`

**Enhanced Features**:
- Each relevant action includes tactical reason and context
- Suggested parameters for complex actions
- Clear statement that priority scores are algorithmic suggestions, not commands
- Emphasis on personal judgment autonomy

**Decision Factors**:
1. Current operational directive priority
2. Threat level assessment  
3. Tactical advantage considerations
4. Impact on overall prison order
5. Professional duty requirements
6. **Personal mental state** (especially when sanity < 20)
7. **Algorithmic recommendations** (as guidance, not imperatives)