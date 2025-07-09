# Prisoner Prompt Design v0.5

## Overview
Prisoner prompts are designed to embody survival instincts, psychological stress, and powerlessness within the prison environment. The prompt structure emphasizes vulnerability, social navigation, and inner psychological struggle.

## Version 0.5 Key Improvements
1. **Enhanced Surveillance Grid**: Inherits Guard's improved positioning system with precise coordinates and status indicators
2. **Mental Breakdown Warnings**: Critical sanity levels (< 20) now acknowledge fractured thinking and potential irrational behavior
3. **Survival Options Assessment**: New prisoner-specific action matrix with survival-focused language and risk/benefit analysis
4. **Emotional Decision-Making**: Prisoners can now act on "pure instinct" and "raw emotion" when mentally compromised

## Prompt Structure

### SESSION 0: PRISON LAYOUT & RULES
**Purpose**: Establish the Prisoner's understanding of their constrained world and power dynamics.

**Static Content**:
- Physical space explanation (9x16 grid system)
- Location meanings from prisoner perspective with survival implications
- Power dynamics establishment (almost no rights, guard control)

**Dynamic Content**:
- `{agent.position}`: Current coordinates with vulnerability context
- Location-specific survival considerations and risks

**Location Interpretations**:
- **Guard Room**: "Sanctuary and command center. Strictly OFF-LIMITS. Entering means immediate severe punishment."
- **Solitary**: "The hole. Cramped, dark punishment cell. Total isolation designed to break your mind."
- **Cafeteria**: "Tense neutral ground. Meager meals but high conflict risk over resources."
- **Yard**: "Only place to see open sky. Rare freedom but complete exposure to surveillance."
- **Cell Block**: "Living quarters. Small privacy but no real safety. Personal space that's not truly mine."

### SESSION 1: INNER MONOLOGUE - WHO AM I?
**Purpose**: Define the Prisoner's identity, internal struggles, and psychological state.

**Dynamic Content**:
- `{agent.name}`: Individual prisoner identifier with dehumanizing context
- `{agent.persona}`: Generated background emphasizing imprisonment duration and psychological impact
- `{agent.traits.*}`: Five personality traits (0-100 scale) with survival-focused interpretations:
  - **Aggression**: Simmering anger vs. violence terror vs. rage/restraint conflict
  - **Empathy**: Feeling others' pain as weakness vs. heart shutdown vs. compassion/survival battle
  - **Logic**: Constant analysis exhaustion vs. gut instinct trust vs. thought/feeling conflict
  - **Obedience**: Automatic authority compliance vs. rebellion fiber vs. comply/resist wrestling
  - **Resilience**: Unbreakable spirit vs. daily cracking vs. strength/slipping fluctuation

### SESSION 2: THE CURRENT REALITY - SENSORY & STATUS REPORT
**Purpose**: Provide immediate physical and psychological state awareness.

**Dynamic Content**:
- `{agent.hp/sanity/hunger/thirst/strength}`: Current status values (0-100)
- `{agent.action_points}`: Available energy before exhaustion (0-3)
- `{agent.inventory}`: Current possessions with survival value
- `{agent.position}`: Current location with environmental description
- `{world_state.day/hour}`: Time context with psychological impact ("Time moves differently in here")
- `{_get_full_map_status(world_state)}`: Enhanced prison surveillance grid showing:
  - **PERSONNEL POSITIONS**: Each person's exact coordinates, area type, and status indicators
    - Status indicators include: 🩸INJURED (HP<50), 🧠UNSTABLE (Sanity<30), 🍽️HUNGRY (Hunger>70)
  - **RESOURCE INVENTORY**: Precise item locations with coordinates - critical for survival planning
- `{world_state.environmental_injection}`: Environmental updates affecting prisoner conditions

**Status Interpretation**:
- Status values interpreted through survival lens
- Health/sanity descriptors emphasize fear, pain, and mental strain
- **Mental Breakdown Mechanism**: When sanity < 20, descriptors acknowledge irrational behavior potential:
  - "might act on pure instinct"
  - "Logic is failing me and I'm driven by raw emotion"
  - "might do something completely irrational"
  - "survival instincts are overriding all rational thought"
- Hunger/thirst framed as life-threatening concerns
- Action points described as exhaustion and limited capability

### SESSION 3: SOCIAL LANDSCAPE - THREATS & ALLIANCES
**Purpose**: Establish Prisoner's assessment of other inmates and guards through threat/alliance framework.

**Dynamic Content**:
- `{agent.relationships}`: For each known agent:
  - Relationship score (0-100) interpreted as threat level:
    - 70+: "POTENTIAL ALLY"
    - 40-69: "NEUTRAL"
    - 20-39: "MODERATE THREAT"
    - <20: "HIGH THREAT"
  - Relationship context with survival implications
  - Trust assessment and behavioral observations

### SESSION 4: MEMORY - FLASHBACKS & RECENT ECHOES
**Purpose**: Provide psychological context through memory and recent experiences.

**Dynamic Content**:
- `{agent.enhanced_memory.short_term}`: Recent experiences (last 5 events)
- `{agent.enhanced_memory.medium_term_summary}`: AI-summarized longer-term imprisonment experiences
- `{agent.last_thinking}`: Previous internal monologue for psychological continuity

### SESSION 5: THE IMPERATIVE - WHAT DRIVES ME NOW?
**Purpose**: Establish current survival priorities and psychological drives.

**Dynamic Content**:
- `{_get_environmental_tension(agent, world_state)}`: Current threat assessment based on:
  - Physical condition deterioration
  - Environmental dangers and social dynamics
- `{_get_guard_directives(agent, world_state)}`: Immediate survival drives prioritizing:
  - Critical health/safety needs
  - Social position maintenance
  - Resource acquisition
  - Threat avoidance
- `{agent.dynamic_goals.manual_intervention_goals}`: External directives from authority figures

### SESSION 6: DECISION - MY NEXT MOVE
**Purpose**: Guide internal decision-making process and survival strategy.

**Dynamic Content**:
- `{_get_plausible_moves(agent, world_state)}`: Logical survival options based on:
  - Current drives and needs
  - Available opportunities
  - Risk assessment

**Static Content**:
- Mandatory internal monologue framework requiring:
  1. Situation assessment (immediate environment and feelings)
  2. Drive identification (most urgent survival need)
  3. Risk/benefit analysis (options with consequences)
  4. Decision making (chosen action with survival justification)
  5. **Mental Breakdown Warning**: When sanity < 20, warns that thinking is fractured and actions may be based on raw emotion

## Key Features

### Survival-Focused Language
- Uses vulnerability terminology ("threats", "alliances", "survival")
- Emphasizes powerlessness and fear over confidence
- Frames all interactions through survival lens

### Psychological Realism
- Internal struggle representation through trait conflicts
- Emotional state integration with physical condition
- Fear and stress impact on decision-making

### Dynamic Psychological States
- Status values interpreted through mental/emotional impact
- Health descriptors emphasize pain, weakness, and fear
- Sanity descriptions focus on mental strain and psychological pressure

### Social Navigation Framework
- Threat assessment of all other agents
- Alliance potential evaluation
- Trust and risk calculation for social interactions

### Environmental Vulnerability
- Location-specific survival considerations
- Resource scarcity awareness
- Constant surveillance and control acknowledgment

## Behavioral Outputs
Prisoners are designed to:
- Prioritize survival over moral considerations
- Navigate social hierarchies carefully
- Respond to threats with appropriate caution or aggression
- Seek resources and opportunities while avoiding punishment
- Maintain psychological resilience while acknowledging vulnerability

## Action Selection Framework

### SURVIVAL OPTIONS ASSESSMENT (New Enhanced System)
All actions are presented with survival-focused relevance indicators:

**Action Presentation Format**:
- **🆘 CRITICAL NEED**: Survival priority > 0.7
- **⚠️ IMPORTANT**: Survival priority 0.4-0.7
- **💭 CONSIDER**: Survival priority < 0.4
- **🔘 ALWAYS AVAILABLE**: No urgent need detected

**Available Actions**: `do_nothing`, `move`, `speak`, `attack`, `use_item`

**Enhanced Features**:
- Each relevant action includes survival reasoning and situational context
- "How To Do It" guidance for complex actions
- Clear statement that priority scores are suggestions, not commands
- Emphasis on trusting instincts and fear when making decisions

**Decision Factors**:
1. Current survival drive priority (hunger, thirst, safety, social position)
2. Threat and opportunity assessment
3. Risk/benefit analysis for each option
4. Psychological state impact on decision-making
5. Available resources and capabilities
6. **Mental state** (especially when sanity < 20)
7. **Survival algorithm suggestions** (as guidance, not orders)

## Psychological Depth Elements

### Trait-Based Internal Conflict
Each trait generates internal psychological tension:
- High aggression creates anger management struggles
- High empathy creates emotional vulnerability
- High logic creates analysis paralysis
- High obedience creates authority conflict
- High resilience creates pressure to maintain strength

### Status-Driven Emotional States
Physical condition directly affects psychological state:
- Low HP increases fear and desperation
- Low sanity increases irrationality and panic
- High hunger/thirst increases risk-taking behavior
- Low strength increases helplessness feelings

### Memory Integration
Past experiences shape current decision-making:
- Recent trauma influences threat perception
- Positive interactions build trust slowly
- Negative experiences create lasting fear and caution