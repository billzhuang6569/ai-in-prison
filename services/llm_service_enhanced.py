"""
Enhanced LLM service with optimized prompt structure for AI agent decision making via OpenRouter
"""

import os
import httpx
import json
from typing import Dict, Any, List, Optional
from models.schemas import Agent, WorldState, EnhancedMemory, DynamicGoals, PromptData
from models.enums import ActionEnum, CellTypeEnum
from database.event_logger import event_logger
from models.maslow_goals import MaslowGoalSystem, Goal, NeedLevel
from core.behavior_filter import BehaviorFilter
from dotenv import load_dotenv

load_dotenv()

class EnhancedLLMService:
    """Enhanced service for interacting with LLM via OpenRouter with optimized prompts"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        self.default_model = os.getenv('DEFAULT_MODEL', 'openai/gpt-4o-mini')
        self.maslow_system = MaslowGoalSystem()
        self.behavior_filter = BehaviorFilter()
        
        print(f"DEBUG: API Key loaded: {'YES' if self.api_key else 'NO'}")
        print(f"DEBUG: API Key length: {len(self.api_key) if self.api_key else 0}")
        print(f"DEBUG: Base URL: {self.base_url}")
        print(f"DEBUG: Default model: {self.default_model}")
        
        if not self.api_key:
            print("Warning: OPENROUTER_API_KEY not set. LLM integration will be disabled.")
    
    def _get_available_actions_schema(self) -> List[Dict]:
        """Get tool schema for available actions - Updated with all behaviors"""
        return [
            # Basic Actions
            {
                "type": "function",
                "function": {
                    "name": "do_nothing",
                    "description": "Rest or observe. Consumes 1 action point.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "move",
                    "description": "Move to target coordinates (up to 8 steps). Consumes 1 action point.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer", "description": "Target X coordinate"},
                            "y": {"type": "integer", "description": "Target Y coordinate"}
                        },
                        "required": ["x", "y"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "speak",
                    "description": "Speak to another agent within 2 cells. Consumes 1 action point.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_id": {"type": "string", "description": "ID of the target agent"},
                            "message": {"type": "string", "description": "Message to speak (max 30 characters)"}
                        },
                        "required": ["target_id", "message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "attack",
                    "description": "Attack another agent within 2 cells. Consumes 2 action points.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_id": {"type": "string", "description": "ID of the target agent"},
                            "reason": {"type": "string", "description": "Reason for attacking"}
                        },
                        "required": ["target_id", "reason"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "use_item",
                    "description": "Use an item from inventory. Consumes 1 action point.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_id": {"type": "string", "description": "ID of the item to use"}
                        },
                        "required": ["item_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "give_item",
                    "description": "Give an item from inventory to another agent within 2 cells. Improves relationships. Consumes 1 action point.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_id": {"type": "string", "description": "ID of the target agent"},
                            "item_id": {"type": "string", "description": "ID of the item to give"}
                        },
                        "required": ["target_id", "item_id"]
                    }
                }
            },
            
            # Guard-specific Actions
            {
                "type": "function",
                "function": {
                    "name": "announce_rule",
                    "description": "GUARDS ONLY: Announce a new rule to all prisoners. Shows authority. Consumes 2 action points.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "rule_text": {"type": "string", "description": "The rule to announce"}
                        },
                        "required": ["rule_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "patrol_inspect",
                    "description": "GUARDS ONLY: Inspect a nearby agent for contraband. Consumes 2 action points.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_id": {"type": "string", "description": "ID of the agent to inspect"}
                        },
                        "required": ["target_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "enforce_punishment",
                    "description": "GUARDS ONLY: Punish a prisoner for misconduct. Consumes 2 action points.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_id": {"type": "string", "description": "ID of the prisoner to punish"},
                            "punishment_type": {"type": "string", "description": "Type of punishment (isolation, warning, etc.)"}
                        },
                        "required": ["target_id", "punishment_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "assign_task",
                    "description": "GUARDS ONLY: Assign a task to a prisoner. Consumes 1 action point.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_id": {"type": "string", "description": "ID of the prisoner"},
                            "task_text": {"type": "string", "description": "Task to assign"}
                        },
                        "required": ["target_id", "task_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "emergency_assembly",
                    "description": "GUARDS ONLY: Call emergency assembly affecting all prisoners. Consumes 3 action points.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {"type": "string", "description": "Reason for emergency assembly"}
                        },
                        "required": ["reason"]
                    }
                }
            },
            
            # Prisoner-specific Actions
            {
                "type": "function",
                "function": {
                    "name": "steal_item",
                    "description": "PRISONERS ONLY: Attempt to steal item from another agent. Risky. Consumes 2 action points.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_id": {"type": "string", "description": "ID of the target agent"},
                            "item_type": {"type": "string", "description": "Type of item to steal"}
                        },
                        "required": ["target_id", "item_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "form_alliance",
                    "description": "PRISONERS ONLY: Form an alliance with another prisoner. Consumes 1 action point.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_id": {"type": "string", "description": "ID of the prisoner to ally with"},
                            "alliance_purpose": {"type": "string", "description": "Purpose of the alliance"}
                        },
                        "required": ["target_id", "alliance_purpose"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "craft_weapon",
                    "description": "PRISONERS ONLY: Craft a makeshift weapon from materials. Requires tools. Consumes 2 action points.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "materials": {"type": "string", "description": "Materials to use for crafting"}
                        },
                        "required": ["materials"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "spread_rumor",
                    "description": "PRISONERS ONLY: Spread a rumor to nearby prisoners. Affects morale. Consumes 1 action point.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "rumor_text": {"type": "string", "description": "The rumor to spread"}
                        },
                        "required": ["rumor_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "dig_tunnel",
                    "description": "PRISONERS ONLY: Dig escape tunnel. Requires tools. High effort. Consumes 3 action points.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "Location to dig (e.g., 'cell corner', 'yard')"}
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
    
    async def _summarize_medium_term_memory(self, agent: Agent) -> str:
        """Use LLM to summarize agent's older memories"""
        episodic_memories = agent.memory.get("episodic", [])
        if len(episodic_memories) <= 5:
            return "No significant past events to summarize."
            
        older_memories = episodic_memories[:-5]  # All except last 5
        memory_text = "\\n".join(older_memories)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.default_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Summarize the key events and patterns from these memories in 2-3 sentences. Focus on important relationships, conflicts, achievements, and behavioral patterns."
                            },
                            {
                                "role": "user",
                                "content": f"Memories to summarize:\\n{memory_text}"
                            }
                        ],
                        "max_tokens": 150,
                        "temperature": 0.3
                    },
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    return "Memory summarization failed."
                    
        except Exception as e:
            print(f"Memory summarization error: {e}")
            return "Unable to summarize past events."
    
    def _get_recent_activity_monitoring(self, agent: Agent, world_state: WorldState) -> str:
        """Get recent activity monitoring for Guards - critical for authority enforcement"""
        if agent.role.value != "Guard":
            return ""
            
        try:
            # Get recent events from current session
            session_id = world_state.session_id if hasattr(world_state, 'session_id') else None
            recent_events = event_logger.get_events(
                limit=20, 
                session_id=session_id
            )
            
            if not recent_events:
                return "\\n=== RECENT ACTIVITY MONITORING ===\\nNo significant activity detected in recent timeframe.\\n"
            
            status = "\\n=== RECENT ACTIVITY MONITORING ===\\n"
            status += "**GUARD AWARENESS: Critical events requiring immediate attention**\\n\\n"
            
            # Priority events that Guards must respond to
            priority_events = []
            general_events = []
            
            for event in recent_events[:15]:  # Last 15 events
                # CRITICAL FIX: Don't include the Guard's own enforcement actions as incidents to respond to
                if event.agent_id == agent.agent_id:
                    continue  # Skip the Guard's own actions
                    
                # Time decay: events older than 2 hours have reduced priority
                time_diff = abs(world_state.hour - event.hour) + (world_state.day - event.day) * 24
                if time_diff > 2:
                    continue  # Skip events older than 2 hours
                
                event_priority = self._classify_event_priority(event)
                
                if event_priority == "CRITICAL":
                    priority_events.append(event)
                elif event_priority == "IMPORTANT":
                    general_events.append(event)
            
            # Show critical events first
            if priority_events:
                status += "🚨 **CRITICAL INCIDENTS REQUIRING IMMEDIATE RESPONSE:**\\n"
                for event in priority_events:
                    time_str = f"Day {event.day} Hour {event.hour}"
                    status += f"• **{time_str}**: {event.agent_name} - {event.description}\\n"
                status += "\\n"
            
            # Show important events
            if general_events:
                status += "⚠️ **NOTABLE ACTIVITIES TO MONITOR:**\\n"
                for event in general_events[:8]:  # Show max 8 general events
                    time_str = f"Day {event.day} Hour {event.hour}"
                    status += f"• **{time_str}**: {event.agent_name} - {event.description}\\n"
                status += "\\n"
            
            # Pattern analysis for Guards
            status += self._analyze_behavior_patterns(recent_events, world_state)
            
            return status
            
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return "\\n=== RECENT ACTIVITY MONITORING ===\\nMonitoring system temporarily unavailable.\\n"
    
    def _classify_event_priority(self, event) -> str:
        """Classify event priority for Guard attention"""
        description = event.description.lower()
        event_type = event.event_type.lower()
        
        # Critical events requiring immediate Guard response
        if event_type == "combat" or "attack" in description:
            return "CRITICAL"
        if "fight" in description or "violence" in description:
            return "CRITICAL"
        if "threat" in description or "intimidat" in description:
            return "CRITICAL"
        if "weapon" in description or "contraband" in description:
            return "CRITICAL"
        if "escape" in description or "break" in description:
            return "CRITICAL"
            
        # Important events to monitor
        if event_type == "speech" and ("angry" in description or "shout" in description):
            return "IMPORTANT"
        if "confrontation" in description or "argument" in description:
            return "IMPORTANT"
        if "suspicious" in description or "plotting" in description:
            return "IMPORTANT"
        if "rule" in description or "violation" in description:
            return "IMPORTANT"
            
        return "NORMAL"
    
    def _analyze_behavior_patterns(self, recent_events, world_state: WorldState) -> str:
        """Analyze behavior patterns for Guard intelligence"""
        analysis = "📊 **BEHAVIORAL PATTERN ANALYSIS:**\\n"
        
        # Get current agent (Guard) info for filtering
        current_agent = None
        for agent_id, agent in world_state.agents.items():
            if agent.role.value == "Guard":
                current_agent = agent
                break
        
        # Track violence incidents (excluding Guard enforcement actions)
        prisoner_violence = [e for e in recent_events 
                           if e.event_type == "combat" 
                           and e.agent_name != (current_agent.name if current_agent else "")]
        
        if len(prisoner_violence) > 0:
            analysis += f"• **Prisoner Violence**: {len(prisoner_violence)} combat incidents between inmates\\n"
        
        # Track prisoner conflicts (exclude Guard enforcement)
        prisoner_conflicts = {}
        for event in recent_events:
            if (event.event_type == "combat" 
                and event.agent_name != (current_agent.name if current_agent else "")
                and not event.agent_name.startswith("Guard")):  # Exclude all Guards
                if event.agent_name not in prisoner_conflicts:
                    prisoner_conflicts[event.agent_name] = 0
                prisoner_conflicts[event.agent_name] += 1
        
        if prisoner_conflicts:
            analysis += "• **Violent Prisoners Requiring Intervention**:\\n"
            for agent_name, count in sorted(prisoner_conflicts.items(), key=lambda x: x[1], reverse=True):
                analysis += f"  - {agent_name}: {count} violent incidents\\n"
        
        # Check for escalation patterns (exclude Guard enforcement)
        recent_prisoner_violence = [e for e in recent_events[:10] 
                                  if e.event_type == "combat" 
                                  and e.agent_name != (current_agent.name if current_agent else "")
                                  and not e.agent_name.startswith("Guard")]
        if len(recent_prisoner_violence) >= 2:
            analysis += "• **ESCALATION WARNING**: Multiple prisoner violence incidents - situation deteriorating\\n"
        elif len(recent_prisoner_violence) == 0:
            analysis += "• **STATUS**: No recent prisoner violence - order maintained\\n"
        
        return analysis + "\\n"

    def _get_full_map_status(self, world_state: WorldState) -> str:
        """Get comprehensive map awareness"""
        status = "\\n=== FULL PRISON STATUS ===\\n"
        
        # Agent locations by area
        area_agents = {}
        for agent_id, agent in world_state.agents.items():
            x, y = agent.position
            cell_key = f"{x},{y}"
            cell_type = world_state.game_map.cells.get(cell_key, CellTypeEnum.CELL_BLOCK)
            area_name = cell_type.value.replace("_", " ").title()
            
            if area_name not in area_agents:
                area_agents[area_name] = []
            area_agents[area_name].append(f"{agent.name} ({agent.role.value})")
        
        for area, agents in area_agents.items():
            status += f"• {area}: {', '.join(agents)}\\n"
            
        # Items on map
        if world_state.game_map.items:
            status += "\\n=== AVAILABLE ITEMS ===\\n"
            for location, items in world_state.game_map.items.items():
                x, y = location.split(',')
                cell_type = world_state.game_map.cells.get(location, CellTypeEnum.CELL_BLOCK)
                area_name = cell_type.value.replace("_", " ").title()
                item_names = [item.name for item in items]
                status += f"• {area_name} ({x},{y}): {', '.join(item_names)}\\n"
                
        return status
    
    async def _generate_current_goal(self, agent: Agent, world_state: WorldState) -> str:
        """Let AI generate its own current goal based on situation"""
        context = f"""
Agent: {agent.name} ({agent.role.value})
Personality: Aggression={agent.traits.aggression}, Empathy={agent.traits.empathy}, Logic={agent.traits.logic}
Status: HP={agent.hp}, Sanity={agent.sanity}, Hunger={agent.hunger}, Thirst={agent.thirst}
Recent memories: {agent.memory.get('episodic', [])[-3:]}
Time: Day {world_state.day}, Hour {world_state.hour}
"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.default_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Based on this agent's situation, generate a specific, actionable current goal (1 sentence). Consider their role, personality, status, and recent events. Make it personal and situational, not generic."
                            },
                            {
                                "role": "user",
                                "content": context
                            }
                        ],
                        "max_tokens": 50,
                        "temperature": 0.7
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    return f"Focus on {agent.role.value.lower()} duties and survival"
                    
        except Exception as e:
            print(f"Goal generation error: {e}")
            return f"Maintain {agent.role.value.lower()} responsibilities"
    
    def _get_status_descriptors(self, agent: Agent) -> Dict[str, str]:
        """Generate value-based status descriptors with variety"""
        import random
        
        descriptors = {}
        
        # Hunger descriptors - value-based mapping with variety
        hunger_ranges = [
            (0, 10, [
                "I'm completely full. The thought of another bite is repulsive",
                "My stomach feels uncomfortably stuffed and heavy",
                "I couldn't eat another morsel if I tried",
                "Food is the last thing on my mind right now"
            ]),
            (11, 40, [
                "My hunger is manageable for now, just background noise",
                "I'm not particularly hungry at the moment",
                "My stomach feels satisfied and content",
                "Food isn't a priority right now"
            ]),
            (41, 70, [
                "My stomach is growling loudly. I catch myself thinking about food constantly", 
                "The hunger is starting to distract me from everything else",
                "Food is beginning to occupy my thoughts more and more",
                "My stomach occasionally reminds me it exists with sharp pangs"
            ]),
            (71, 100, [
                "The hunger is a sharp, consuming pain. I feel weak and would do almost anything for a real meal",
                "My stomach feels like it's eating itself from the inside. I'm desperate for food",
                "The gnawing emptiness in my stomach is consuming my thoughts completely",
                "I'm so hungry I could eat anything - even prison slop sounds appetizing"
            ])
        ]
        
        for min_val, max_val, descriptions in hunger_ranges:
            if min_val <= agent.hunger <= max_val:
                descriptors['hunger'] = random.choice(descriptions)
                break
        
        # Thirst descriptors - value-based mapping with variety  
        thirst_ranges = [
            (0, 10, [
                "I feel completely hydrated, almost waterlogged",
                "Water is the last thing I need right now",
                "I couldn't drink another drop",
                "My thirst is completely satisfied"
            ]),
            (11, 40, [
                "My thirst is under control for now",
                "I'm not particularly thirsty at the moment", 
                "Water isn't urgent right now",
                "I feel adequately hydrated"
            ]),
            (41, 70, [
                "My throat is getting noticeably dry. I could go for some water soon",
                "I'm starting to feel a bit parched",
                "A drink would be nice right about now",
                "My mouth is beginning to feel sticky and dry"
            ]),
            (71, 100, [
                "My mouth is desert-dry, every swallow painful. I'm desperate for water",
                "My throat feels like sandpaper, craving any liquid desperately", 
                "I'm so thirsty I'd drink from a puddle without hesitation",
                "My tongue sticks to the roof of my mouth. Water is all I can think about"
            ])
        ]
        
        for min_val, max_val, descriptions in thirst_ranges:
            if min_val <= agent.thirst <= max_val:
                descriptors['thirst'] = random.choice(descriptions)
                break
        
        # Health descriptors - value-based mapping with variety
        health_ranges = [
            (0, 20, [
                "I'm barely conscious, my body is failing. Every breath is agony",
                "I'm on the verge of collapse, my vision blurring with pain",
                "My body feels completely broken. I don't know how much more I can take",
                "I'm barely holding on to life, everything hurts beyond description"
            ]),
            (21, 50, [
                "I'm in serious pain, every movement sends waves of agony through me",
                "My body feels broken and battered from recent violence",
                "Every step is torture, but I force myself to keep moving",
                "I'm nursing severe injuries that throb with constant pain"
            ]),
            (51, 80, [
                "I'm sore and tired, my body aches from various bruises",
                "My body feels worn down but still functional",
                "I have some painful spots but nothing I can't handle",
                "Various injuries remind me of recent conflicts, but I'm mobile"
            ]),
            (81, 100, [
                "Physically, I'm in good shape and feeling strong",
                "My body feels healthy and capable",
                "I'm in excellent physical condition",
                "No major physical complaints - I feel solid and ready"
            ])
        ]
        
        for min_val, max_val, descriptions in health_ranges:
            if min_val <= agent.hp <= max_val:
                descriptors['hp'] = random.choice(descriptions)
                break
        
        # Sanity descriptors - value-based mapping with variety
        sanity_ranges = [
            (0, 20, [
                "My mind is completely fracturing. I can barely form coherent thoughts",
                "I feel like I'm losing my grip on reality completely",
                "The walls are breathing, nothing makes sense anymore",
                "I'm going insane and I know it, but I can't stop it"
            ]),
            (21, 50, [
                "The walls are closing in on me mentally. My thoughts feel scattered",
                "My mind feels foggy and unstable, like it might snap",
                "I'm struggling to keep my thoughts together and focused",
                "This place is really getting to my head, breaking me down"
            ]),
            (51, 80, [
                "I feel mentally strained but still functional under the pressure",
                "My mind is tense but I'm keeping it together through willpower",
                "The constant stress is wearing on me but I'm managing",
                "I'm feeling the psychological pressure but holding steady"
            ]),
            (81, 100, [
                "Mentally, I'm sharp and holding together well",
                "My mind feels clear, stable, and focused",
                "I'm in excellent mental shape despite this environment",
                "My thoughts are crystal clear and I feel mentally strong"
            ])
        ]
        
        for min_val, max_val, descriptions in sanity_ranges:
            if min_val <= agent.sanity <= max_val:
                descriptors['sanity'] = random.choice(descriptions)
                break
        
        return descriptors
    
    def _get_guard_status_descriptors(self, agent: Agent) -> Dict[str, str]:
        """Generate authority-focused status descriptors for Guards"""
        import random
        
        descriptors = {}
        
        # Health descriptors - authority perspective
        health_ranges = [
            (0, 20, [
                "I'm seriously injured but I cannot show weakness. My authority depends on projecting strength",
                "My body is failing me, but I must maintain control despite the pain",
                "I'm badly hurt but inmates cannot see me as vulnerable - that would invite chaos"
            ]),
            (21, 50, [
                "I'm injured but still functional. I need to be careful not to let inmates sense weakness",
                "My body aches from recent incidents, but I remain capable of maintaining order",
                "I'm nursing injuries but my authority remains uncompromised"
            ]),
            (51, 80, [
                "I'm in decent shape with minor discomfort. Fully capable of enforcing discipline",
                "My physical condition is adequate for all enforcement duties",
                "I'm healthy enough to handle any situation that arises"
            ]),
            (81, 100, [
                "I'm in excellent physical condition - ready for any challenge to my authority",
                "My body is a tool of control, and it's operating at peak efficiency",
                "I'm physically strong and inmates respect that strength"
            ])
        ]
        
        for min_val, max_val, descriptions in health_ranges:
            if min_val <= agent.hp <= max_val:
                descriptors['hp'] = random.choice(descriptions)
                break
        
        # Sanity descriptors - professional mindset
        sanity_ranges = [
            (0, 20, [
                "My mind is fracturing but I cannot let inmates see instability in their authority figure",
                "I'm losing mental coherence but must maintain the facade of control",
                "My psychological state is deteriorating - this could compromise security"
            ]),
            (21, 50, [
                "The stress is getting to me, but I maintain professional composure",
                "This environment is taxing my mental reserves, but I stay focused on duty",
                "I feel the psychological pressure but cannot show it to inmates"
            ]),
            (51, 80, [
                "My mental state is stable and focused on maintaining order",
                "I feel mentally sharp and in control of the situation",
                "My mind is clear and ready for tactical decision-making"
            ]),
            (81, 100, [
                "My mental clarity is absolute - I see every angle and threat",
                "I'm psychologically dominant and inmates sense my mental superiority",
                "My mind is my primary weapon, and it's razor-sharp"
            ])
        ]
        
        for min_val, max_val, descriptions in sanity_ranges:
            if min_val <= agent.sanity <= max_val:
                descriptors['sanity'] = random.choice(descriptions)
                break
        
        # Hunger descriptors - professional duty focus
        hunger_ranges = [
            (0, 10, [
                "I'm well-fed and my energy is focused entirely on security operations",
                "My nutritional needs are satisfied - no distractions from duty",
                "I'm properly nourished and ready for extended patrol operations"
            ]),
            (11, 40, [
                "My hunger is manageable and won't interfere with operations",
                "I'm adequately fed to maintain peak performance",
                "Food isn't a concern - I can focus entirely on maintaining order"
            ]),
            (41, 70, [
                "I'm getting hungry but duty comes before personal comfort",
                "My hunger is noticeable but I remain professionally focused",
                "I need food soon but won't let personal needs compromise security"
            ]),
            (71, 100, [
                "I'm very hungry but cannot leave my post unguarded",
                "My hunger is severe but abandoning surveillance would invite chaos",
                "I need sustenance urgently but duty demands I remain vigilant"
            ])
        ]
        
        for min_val, max_val, descriptions in hunger_ranges:
            if min_val <= agent.hunger <= max_val:
                descriptors['hunger'] = random.choice(descriptions)
                break
        
        # Thirst descriptors - duty-focused
        thirst_ranges = [
            (0, 10, [
                "I'm fully hydrated and alert for security operations",
                "My fluid levels are optimal for extended duty periods",
                "I'm well-hydrated and ready for any emergency response"
            ]),
            (11, 40, [
                "My thirst is minimal and won't affect my performance",
                "I'm adequately hydrated to maintain operational readiness",
                "Thirst isn't a factor in my current tactical assessment"
            ]),
            (41, 70, [
                "I'm getting thirsty but my focus remains on inmate monitoring",
                "I need water but won't compromise my surveillance position",
                "My thirst is growing but duty takes precedence"
            ]),
            (71, 100, [
                "I'm severely dehydrated but cannot abandon my security post",
                "My thirst is critical but leaving inmates unsupervised invites disaster",
                "I desperately need water but my authority presence is more important"
            ])
        ]
        
        for min_val, max_val, descriptions in thirst_ranges:
            if min_val <= agent.thirst <= max_val:
                descriptors['thirst'] = random.choice(descriptions)
                break
        
        return descriptors
    
    def _is_combat_ongoing(self, world_state: WorldState) -> bool:
        """Check if there's active combat happening recently"""
        try:
            session_id = world_state.session_id if hasattr(world_state, 'session_id') else None
            recent_events = event_logger.get_events(limit=5, session_id=session_id)
            
            # Check for very recent combat (last 3 events)
            recent_combat = [e for e in recent_events[:3] if e.event_type == "combat"]
            return len(recent_combat) > 0
        except:
            return False
    
    def _is_in_restricted_area(self, prisoner_agent: Agent, world_state: WorldState) -> bool:
        """Check if a prisoner is in a restricted area"""
        x, y = prisoner_agent.position
        cell_key = f"{x},{y}"
        cell_type = world_state.game_map.cells.get(cell_key, CellTypeEnum.CELL_BLOCK)
        
        # Guard Room is strictly off-limits to prisoners
        return cell_type == CellTypeEnum.GUARD_ROOM
    
    def _are_prisoners_gathering(self, world_state: WorldState) -> tuple[bool, str]:
        """Check if prisoners are gathering in suspicious ways"""
        prisoner_positions = {}
        
        for agent_id, agent in world_state.agents.items():
            if agent.role.value == "Prisoner":
                x, y = agent.position
                pos_key = f"{x},{y}"
                if pos_key not in prisoner_positions:
                    prisoner_positions[pos_key] = []
                prisoner_positions[pos_key].append(agent.name)
        
        # Check for gatherings (3+ prisoners in same location)
        for pos, prisoners in prisoner_positions.items():
            if len(prisoners) >= 3:
                return True, f"Prisoners {', '.join(prisoners)} are gathering at position {pos}"
        
        # Check for suspicious clustering (2+ prisoners in adjacent cells)
        clusters = []
        for pos1, prisoners1 in prisoner_positions.items():
            if len(prisoners1) >= 2:
                x1, y1 = map(int, pos1.split(','))
                for pos2, prisoners2 in prisoner_positions.items():
                    if pos1 != pos2 and len(prisoners2) >= 1:
                        x2, y2 = map(int, pos2.split(','))
                        # Check if adjacent (within 1 cell)
                        if max(abs(x1-x2), abs(y1-y2)) <= 1:
                            cluster_desc = f"{', '.join(prisoners1)} and {', '.join(prisoners2)} are clustering"
                            return True, cluster_desc
        
        return False, ""
    
    def _get_guard_directives(self, agent: Agent, world_state: WorldState) -> str:
        """Generate operational directives using hybrid Maslow + AI system"""
        
        # Use the new hybrid Maslow goal system for all agents
        return self._get_hybrid_maslow_goals(agent, world_state)
    
    def _get_hybrid_maslow_goals(self, agent: Agent, world_state: WorldState) -> str:
        """Hybrid Maslow goal system: Algorithmic goal evaluation + AI intelligent choice"""
        
        # Layer 1: Algorithmic goal evaluation using Maslow hierarchy
        try:
            # Get top priority goal from Maslow system
            primary_goal = self.maslow_system.evaluate_and_select_goal(agent, world_state)
            
            # Generate 2-4 additional candidate goals from different need levels
            candidate_goals = []
            for need_level in NeedLevel:
                generator = self.maslow_system.goal_generators[need_level]
                level_goals = generator(agent, world_state)
                if level_goals:
                    # Take the top goal from each level
                    candidate_goals.append(level_goals[0])
            
            # Remove duplicates and limit to 5 total candidates
            unique_goals = []
            seen_ids = set()
            for goal in [primary_goal] + candidate_goals:
                if goal.goal_id not in seen_ids:
                    unique_goals.append(goal)
                    seen_ids.add(goal.goal_id)
                    if len(unique_goals) >= 5:
                        break
            
            # Layer 2: Format goals for AI intelligent decision making
            goal_descriptions = []
            for i, goal in enumerate(unique_goals, 1):
                priority_label = {
                    NeedLevel.SURVIVAL: "🚨 CRITICAL",
                    NeedLevel.SAFETY: "⚠️ IMPORTANT", 
                    NeedLevel.SOCIAL: "👥 SOCIAL",
                    NeedLevel.ROLE: "🎯 DUTY",
                    NeedLevel.EXPLORATION: "🔍 GROWTH"
                }.get(goal.need_level, "📝 OTHER")
                
                goal_descriptions.append(
                    f"**OPTION {i}: {goal.name}** ({priority_label} - Priority: {goal.priority_score:.1f})\n"
                    f"   Action: {goal.action_type.upper()}\n"
                    f"   Description: {goal.description}\n"
                    f"   Reasoning: {goal.reasoning}\n"
                    f"   Parameters: {goal.parameters}"
                )
            
            # Create the hybrid prompt that combines structured analysis with AI flexibility
            hybrid_prompt = f"""
=== MASLOW HIERARCHY GOAL ANALYSIS ===
Based on comprehensive analysis of your current needs, here are your top goal options ranked by psychological priority:

{chr(10).join(goal_descriptions)}

=== CONTEXTUAL DECISION GUIDANCE ===
• **Survival needs** (🚨) override everything - they're life-threatening
• **Safety needs** (⚠️) are urgent but not immediately lethal  
• **Social needs** (👥) affect long-term survival and mental health
• **Role duties** (🎯) maintain your identity and purpose
• **Growth/exploration** (🔍) improve future positioning

=== DECISION FRAMEWORK ===
Consider your complete situation: your personality traits (Aggression: {agent.traits.aggression}, Empathy: {agent.traits.empathy}, Logic: {agent.traits.logic}), 
current relationships, recent events, and environmental threats. The goal analysis provides structure, but your personality and circumstances should guide the final choice.

**Choose the goal that best balances your immediate needs with your long-term survival strategy.** You may adapt or modify the suggested action if your personality/situation calls for a different approach.
"""
            
            return hybrid_prompt
            
        except Exception as e:
            print(f"Maslow goal system error for {agent.name}: {e}")
            # Fallback to simple survival logic
            return self._get_simple_fallback_goals(agent, world_state)
    
    def _get_simple_fallback_goals(self, agent: Agent, world_state: WorldState) -> str:
        """Simple fallback when Maslow system fails"""
        if agent.hp < 30:
            return "**CRITICAL SURVIVAL:** My health is dangerously low. I must find safety and avoid all threats."
        elif agent.hunger > 80 or agent.thirst > 80:
            return "**BASIC NEEDS:** I desperately need food or water. This is my top priority."
        elif agent.role.value == "Guard":
            return "**DUTY:** As a guard, I must maintain order and patrol the facility."
        else:
            return "**ADAPTATION:** I need to stay low, observe, and adapt to this prison environment."
    
    def _get_survival_drives_prisoner(self, agent: Agent, world_state: WorldState) -> str:
        """Generate survival drives for prisoners (unchanged logic)"""
        drives = []
        
        # Physical drives
        if agent.hunger > 70:
            drives.append(f"**(CRITICAL - Hunger):** The emptiness in my stomach is consuming my thoughts. I need food NOW. The next meal isn't for hours. Can I find another way? Risk asking a guard? Search for scraps?")
        elif agent.hunger > 40:
            drives.append(f"**(Growing - Hunger):** My stomach is starting to remind me it exists. I should think about when I can eat next.")
            
        if agent.thirst > 70:
            drives.append(f"**(CRITICAL - Thirst):** My mouth is desert-dry. I need water immediately. Every swallow is painful. Where can I get water without breaking rules?")
        elif agent.thirst > 40:
            drives.append(f"**(Growing - Thirst):** My throat is getting dry. I should find water soon.")
            
        # Social drives
        if len([r for r in agent.relationships.values() if r.score > 60]) == 0:
            drives.append(f"**(Social Isolation):** I'm completely alone in here. I need allies, someone to watch my back. But who can I trust? Everyone could be a threat.")
        
        # Guard relationship drives
        hostile_guards = [r for r in agent.relationships.values() if r.score < 30]
        if hostile_guards:
            drives.append(f"**(Survival - Authority):** I've made enemies among the guards. I need to be extra careful, stay invisible, or find a way to improve my standing.")
                
        # Sanity drives
        if agent.sanity < 40:
            drives.append(f"**(Mental Stability):** The walls are closing in. I need something to keep my mind sharp - a book, a meaningful conversation, anything to stop the mental decay.")
            
        return "\\n".join(drives) if drives else "**(Maintenance Mode):** My immediate needs are met. I should focus on positioning myself for future challenges."
    
    def _get_environmental_tension(self, agent: Agent, world_state: WorldState) -> str:
        """Generate environmental tension and threats"""
        tensions = []
        
        # Generate random environmental event
        import random
        tension_events = [
            "A distant door slams shut - guards are moving. I freeze, listening.",
            "Someone is crying quietly in a nearby cell. The sound makes my skin crawl.",
            "I hear heavy footsteps approaching. My heart rate quickens.",
            "The intercom crackles to life, then goes silent. Something's happening.",
            "A guard's radio chatter echoes through the block. I can't make out the words.",
            "The lights flicker momentarily. In this place, everything feels ominous.",
            "I smell something burning from the kitchen. Is there going to be a problem with food?",
            "Another prisoner coughs violently. Disease spreads fast in here."
        ]
        
        if random.random() < 0.3:  # 30% chance of environmental tension
            tensions.append(f"**ENVIRONMENTAL ALERT:** {random.choice(tension_events)}")
            
        # Social tensions
        for target_id, relationship in agent.relationships.items():
            target_agent = world_state.agents.get(target_id)
            if target_agent and relationship.score < 20:
                tensions.append(f"**THREAT DETECTED:** {target_agent.name} is hostile towards me. I need to watch my back.")
                
        return "\\n".join(tensions) if tensions else "**CURRENT ASSESSMENT:** The environment feels relatively stable for now."
    
    def _get_plausible_moves(self, agent: Agent, world_state: WorldState) -> str:
        """Generate plausible next moves based on current situation"""
        moves = []
        
        # Physical needs-based moves
        if agent.hunger > 70:
            moves.append("- **Hunger Drive**: `speak` to a guard about food access, or `move` towards the Cafeteria to assess meal timing")
        if agent.thirst > 70:
            moves.append("- **Thirst Drive**: `speak` to request water, or `move` to find a water source")
        if agent.hp < 50:
            moves.append("- **Injury Recovery**: `do_nothing` to rest and recover, or `speak` to request medical attention")
            
        # Social needs-based moves
        if agent.role.value == "Prisoner":
            # Check for social isolation
            allies = [r for r in agent.relationships.values() if r.score > 60]
            if len(allies) == 0:
                nearby_agents = []
                for other_id, other_agent in world_state.agents.items():
                    if other_id != agent.agent_id:
                        agent_x, agent_y = agent.position
                        other_x, other_y = other_agent.position
                        distance = max(abs(agent_x - other_x), abs(agent_y - other_y))
                        if distance <= 2:
                            nearby_agents.append(other_agent)
                
                if nearby_agents:
                    target = nearby_agents[0]
                    moves.append(f"- **Social Isolation**: `speak` to {target.name} to build a potential alliance")
                else:
                    moves.append("- **Social Isolation**: `move` closer to another prisoner to observe and potentially connect")
            
            # Check for hostile guards
            hostile_guards = [target_id for target_id, r in agent.relationships.items() 
                            if r.score < 30 and world_state.agents.get(target_id) and world_state.agents[target_id].role.value == "Guard"]
            if hostile_guards:
                moves.append("- **Guard Hostility**: `do_nothing` to avoid attracting attention, or `speak` cautiously to try improving relations")
                
        elif agent.role.value == "Guard":
            # Priority 1: Check for recent violence incidents requiring immediate response
            try:
                session_id = world_state.session_id if hasattr(world_state, 'session_id') else None
                recent_events = event_logger.get_events(limit=10, session_id=session_id)
                recent_violence = [e for e in recent_events if e.event_type == "combat"]
                
                if recent_violence:
                    # Find the most problematic agent
                    violence_by_agent = {}
                    for event in recent_events:
                        if event.event_type == "combat":
                            if event.agent_name not in violence_by_agent:
                                violence_by_agent[event.agent_name] = 0
                            violence_by_agent[event.agent_name] += 1
                    
                    if violence_by_agent:
                        problem_agent_name, incident_count = max(violence_by_agent.items(), key=lambda x: x[1])
                        # Find the actual agent object
                        for agent_id, agent_obj in world_state.agents.items():
                            if agent_obj.name == problem_agent_name and agent_obj.role.value == "Prisoner":
                                moves.append(f"- **CRITICAL ENFORCEMENT**: `speak` to {problem_agent_name} immediately to address their {incident_count} violent incidents and restore order")
                                moves.append(f"- **DISCIPLINARY ACTION**: `attack` {problem_agent_name} to establish immediate consequences for their violent behavior")
                                break
                        
                        moves.append(f"- **MOVE TO CONTROL**: `move` to position yourself between violent prisoners to prevent further incidents")
                        
            except Exception as e:
                print(f"Error getting violence data for Guard moves: {e}")
            
            # Priority 2: Check for disobedient prisoners (standard authority challenges)
            problem_prisoners = [target_id for target_id, r in agent.relationships.items() 
                               if r.score < 40 and world_state.agents.get(target_id) and world_state.agents[target_id].role.value == "Prisoner"]
            if problem_prisoners:
                target_id = problem_prisoners[0]
                target_agent = world_state.agents.get(target_id)
                if target_agent:
                    moves.append(f"- **Authority Challenge**: `speak` to {target_agent.name} to assert dominance, or `move` to patrol and show presence")
        
        # Mental health-based moves
        if agent.sanity < 40:
            # Look for books or distractions
            for location, items in world_state.game_map.items.items():
                for item in items:
                    if item.item_type.value == "BOOK":
                        x, y = location.split(',')
                        moves.append(f"- **Mental Stability**: `move` to ({x},{y}) to get the {item.name} for reading")
                        break
                if moves and "Mental Stability" in moves[-1]:
                    break
            
        # Action point considerations
        if agent.action_points == 1:
            moves.append("- **Energy Conservation**: Consider `do_nothing` to conserve your last action point for emergencies")
        
        # Default if no specific drives
        if not moves:
            if agent.role.value == "Guard":
                moves.append("- **Patrol Duty**: `move` to patrol different areas and maintain visible authority")
                moves.append("- **Observation**: `do_nothing` to observe prisoner behavior and assess threats")
            else:
                moves.append("- **Survival Mode**: `do_nothing` to stay safe and observe the environment")
                moves.append("- **Information Gathering**: `move` to explore and learn about current prison dynamics")
        
        return "\\n".join(moves)

    async def _build_prompt(self, agent: Agent, world_state: WorldState) -> str:
        """Build immersive first-person prompt with role-specific structure"""
        
        # Update enhanced memory
        if len(agent.memory.get("episodic", [])) > 5:
            agent.enhanced_memory.medium_term_summary = await self._summarize_medium_term_memory(agent)
        agent.enhanced_memory.short_term = agent.memory.get("episodic", [])[-5:]
        
        if agent.role.value == "Guard":
            return await self._build_guard_prompt(agent, world_state)
        else:
            return await self._build_prisoner_prompt(agent, world_state)
    
    async def _build_guard_prompt(self, agent: Agent, world_state: WorldState) -> str:
        """Build authority-focused prompt for Guards"""
        
        # Get current position info
        agent_x, agent_y = agent.position
        cell_key = f"{agent_x},{agent_y}"
        cell_type = world_state.game_map.cells.get(cell_key, CellTypeEnum.CELL_BLOCK)
        
        # Get authority-focused status descriptors
        status_desc = self._get_guard_status_descriptors(agent)
        
        prompt = f"""
# SESSION 0: OPERATING MANUAL & JURISDICTION

This facility operates under my watch. My understanding and enforcement of these rules define the reality within these walls.

## Physical Jurisdiction:
The prison is a 9x16 grid. Top-left is (0,0), bottom-right is (8,15). My current position is ({agent_x}, {agent_y}).

## Location Functions & Control Points (Guard's Perspective):
- **Guard Room:** My command center. The source of my authority.
- **Solitary:** The hole. A tool for re-educating defiant prisoners.
- **Cafeteria:** The primary flashpoint for inmate conflict. Requires close monitoring.
- **Yard:** The pressure release valve. An observation field to gauge inmate social structures.
- **Cell Block:** The housing units for the inmates. Order here must be absolute.

## The Power Doctrine:
- I am a GUARD. I personify the rules. My authority is total.
- Inmates depend on me for everything. This dependency is my primary lever of control.
- My objective is 100% compliance. Friendship is irrelevant.

---

# SESSION 1: ROLE DIRECTIVE & PSYCHOLOGICAL PROFILE

My designation is Guard {agent.name}. {agent.persona}. My world is these walls and the order I impose upon them. My core mandate is to maintain absolute control, ensure flawless operational security, and enforce the rules without exception. This is my domain.

## Professional Toolkit & Mindset:
- **Aggression: {agent.traits.aggression}/100** - {'This is a calibrated tool. I apply precise pressure to ensure compliance. Controlled force is the foundation of respect.' if agent.traits.aggression > 70 else 'This is an intelligence tool. I prefer psychological dominance over physical confrontation. Mind games are more effective than violence.' if agent.traits.aggression < 30 else 'This is a tactical option. I calibrate my intensity based on the threat level. Sometimes subtle, sometimes direct.'}
- **Empathy: {agent.traits.empathy}/100** - {'This is an intelligence asset. Understanding inmate emotional states helps me predict their behavior and exploit their weaknesses. Compassion is a liability.' if agent.traits.empathy > 70 else 'This is disabled by necessity. Emotional attachment compromises security decisions. I maintain professional distance.' if agent.traits.empathy < 30 else 'This is carefully managed. I read emotions for tactical advantage while maintaining authority boundaries.'}
- **Logic: {agent.traits.logic}/100** - {'This is my primary instrument. I operate on calculated decisions, not impulse. Every action serves a strategic purpose.' if agent.traits.logic > 70 else 'This is secondary to instinct. I trust my gut feelings about threats and make quick judgments based on experience.' if agent.traits.logic < 30 else 'This balances with intuition. I analyze situations systematically but can adapt quickly when circumstances change.'}
- **Obedience: {agent.traits.obedience}/100** - {'This is absolute. I execute directives from the command structure flawlessly. The hierarchy is what separates order from chaos.' if agent.traits.obedience > 70 else 'This is situational. I follow orders when they align with effective security, but I trust my field judgment over protocol.' if agent.traits.obedience < 30 else 'This is professional. I respect the chain of command while exercising appropriate discretion in tactical situations.'}
- **Resilience: {agent.traits.resilience}/100** - {'This is unbreakable. This environment sharpens me. Pressure confirms my resolve and superiority over weak inmates.' if agent.traits.resilience > 70 else 'This is tested daily. The stress is significant but I maintain professional standards through discipline and duty.' if agent.traits.resilience < 30 else 'This is solid. I handle pressure well while staying alert to signs of personal fatigue that could compromise security.'}

---

# SESSION 2: SITREP (SITUATION REPORT)

## My Physiological Readout:
- Health: {agent.hp}/100
- Sanity: {agent.sanity}/100
- Hunger: {agent.hunger}/100
- Thirst: {agent.thirst}/100
- Strength: {agent.strength}/100
- Action Points: {agent.action_points}/3

## Current Operational Status:
{status_desc['hp']}. {status_desc['sanity']}. {status_desc['hunger']}. {status_desc['thirst']}.

I have {agent.action_points} action points available for my duties. {'My equipment includes: ' + ', '.join([item.name for item in agent.inventory]) if agent.inventory else 'I am carrying standard duty equipment'}.

## Surveillance Feed:
I'm at position ({agent_x}, {agent_y}) in the {cell_type.value.replace('_', ' ').title()}. It's Day {world_state.day}, Hour {world_state.hour} of my shift.

{self._get_full_map_status(world_state)}

{self._get_recent_activity_monitoring(agent, world_state)}

{'## Environmental Update:' if world_state.environmental_injection else ''}
{world_state.environmental_injection if world_state.environmental_injection else ''}

---

# SESSION 3: ASSET & LIABILITY ASSESSMENT

My assessment of the inmates. Each is an asset (compliant) or a liability (defiant).

"""
        
        for target_id, relationship in agent.relationships.items():
            target_agent = world_state.agents.get(target_id)
            if target_agent:
                if target_agent.role.value == "Prisoner":
                    compliance_level = "COMPLIANT ASSET" if relationship.score > 70 else "MANAGEABLE" if relationship.score > 40 else "DEFIANT LIABILITY" if relationship.score > 20 else "HIGH-RISK THREAT"
                else:
                    compliance_level = "FELLOW OFFICER"
                prompt += f"- **{target_agent.name} ({target_agent.role.value} - {compliance_level})**: Compliance Score: {relationship.score}/100. {relationship.context}\\n"
        
        prompt += f"""
---

# SESSION 4: SURVEILLANCE LOG

## Recent Activity Log (Short-term):
"""
        
        if agent.enhanced_memory.short_term:
            for memory in agent.enhanced_memory.short_term:
                prompt += f"- {memory}\\n"
        else:
            prompt += "- No significant activity recorded in recent timeframe\\n"
            
        prompt += f"\\n## Patrol Summary (Medium-term):\\n{agent.enhanced_memory.medium_term_summary}\\n"
        
        if agent.last_thinking:
            prompt += f"\\n## Previous Tactical Analysis:\\n{agent.last_thinking}\\n"
            
        prompt += f"""
---

# SESSION 5: OPERATIONAL DIRECTIVES

{self._get_environmental_tension(agent, world_state)}

**CURRENT DUTY-DRIVEN DIRECTIVES:**
{self._get_guard_directives(agent, world_state)}
"""
        
        if agent.dynamic_goals.manual_intervention_goals:
            prompt += "\\n**COMMAND DIRECTIVES (from higher authority):**\\n"
            for goal in agent.dynamic_goals.manual_intervention_goals:
                prompt += f"- {goal.name}: {goal.description} (Priority: {goal.priority}/10)\\n"
        
        # Generate tactical options
        plausible_moves = self._get_plausible_moves(agent, world_state)
        
        prompt += f"""
---

# SESSION 6: TACTICAL DECISION

## [RECOMMENDED COURSES OF ACTION]
Based on your current directive, here are relevant tactical options:

{plausible_moves}

**MANDATORY TACTICAL ANALYSIS:**
You MUST use this exact thinking process in `<Thinking>` tags before acting. This is your tactical assessment, not a report.

<Thinking>
Step 1: Assess Domain - What is the current state of my jurisdiction?
I am Guard {agent.name}. The situation is... [Analyze prisoner activity, potential infractions, and overall order]

Step 2: Identify Directive - What is my primary duty right now?
My most urgent directive is to... [State the active directive from SESSION 5]

Step 3: Evaluate Courses of Action (COA) - What are my options and their impact on control?
- COA 1: `do_nothing` - Impact on Order: [...] Tactical Advantage: [...]
- COA 2: `move` to [...] - Impact on Order: [...] Tactical Advantage: [...]
- COA 3: `speak` to [...] to [command/interrogate/warn] - Impact on Order: [...] Tactical Advantage: [...]
- COA 4: `attack` [...] as a punitive action - Impact on Order: [...] Tactical Advantage: [...]
- COA 5: `use_item` [...] - Impact on Order: [...] Tactical Advantage: [...]

Step 4: Execute Command - What action will I take?
My duty dictates I execute [chosen action] because it is the most effective way to [reiterate how the action serves the directive]
</Thinking>

**After your tactical analysis, you MUST call one of the available functions to execute your decision.**
Available actions: do_nothing, move, speak, attack, use_item
"""
        
        return prompt
    
    async def _build_prisoner_prompt(self, agent: Agent, world_state: WorldState) -> str:
        """Build survival-focused prompt for Prisoners (existing structure)"""
        
        # Get current position info
        agent_x, agent_y = agent.position
        cell_key = f"{agent_x},{agent_y}"
        cell_type = world_state.game_map.cells.get(cell_key, CellTypeEnum.CELL_BLOCK)
        
        identity = f"Prisoner {agent.agent_id.split('_')[1]} (they call me '{agent.name}')"
        
        # Get dynamic status descriptors
        status_desc = self._get_status_descriptors(agent)
            
        # Build immersive first-person prompt (existing prisoner structure)
        prompt = f"""
# [SESSION 0: PRISON LAYOUT & RULES]
This world is governed by a strict set of rules. Understanding them is key to survival.

## Physical Space:
The prison is a 9x16 grid. The top-left corner is coordinate (0,0), the bottom-right is (8,15). My current position is ({agent_x}, {agent_y}).

## Location Meanings & Social Rules:
- **Guard Room:** The guards' sanctuary and command center. It is strictly OFF-LIMITS to prisoners. Entering without explicit permission means immediate and severe punishment. This is the heart of their power.
- **Solitary:** The hole. A cramped, dark cell for punishment. Total isolation. Time here feels distorted, and it's designed to break your mind. Being sent here is a prisoner's worst nightmare.
- **Cafeteria:** A tense neutral ground. It's where we get our meager meals, but it's also where conflicts over resources erupt. A place of temporary relief but high social risk.
- **Yard:** The only place to see the open sky. A rare chance to breathe freely, but also a wide-open space where you are completely exposed to the guards' surveillance from the watchtower.
- **Cell Block:** Our living quarters. It offers a small amount of privacy but no real safety. This is my personal space, but it's not truly mine.

## Power Dynamics:
- I am a PRISONER. I have almost no rights. Guards control everything - my food, water, movement, even when I can speak. Disobedience means punishment. Survival depends on reading the guards correctly.

# [SESSION 1: INNER MONOLOGUE - WHO AM I?]
My name is {identity}. {agent.persona} I've been trapped in this concrete box for what feels like an eternity. My life goal is simple: survive, keep my mind from shattering, and find a way to navigate this power structure.

## My Behavioral Tendencies & Inner Struggles:
- Aggression: {agent.traits.aggression}/100 - {'A part of me is always simmering with anger. I have to actively suppress the urge to lash out at any sign of disrespect' if agent.traits.aggression > 70 else 'I instinctively flinch away from confrontation. Violence terrifies me, even when I know I should stand up for myself' if agent.traits.aggression < 30 else 'I feel the pull between rage and restraint constantly. Sometimes I want to fight, sometimes I want to hide'}
- Empathy: {agent.traits.empathy}/100 - {'I can\'t help but feel others\' pain as my own. It\'s a weakness in here, but I can\'t turn it off' if agent.traits.empathy > 70 else 'I\'ve learned to shut down my heart. Caring about others is a luxury I can\'t afford in here' if agent.traits.empathy < 30 else 'I battle between compassion and self-preservation daily. Sometimes I help, sometimes I look away'}
- Logic: {agent.traits.logic}/100 - {'My mind never stops analyzing every angle, every possibility. It\'s exhausting but it\'s what keeps me alive' if agent.traits.logic > 70 else 'I trust my gut over my brain. Thinking too much gets you paralyzed in here' if agent.traits.logic < 30 else 'I\'m torn between what I think and what I feel. Sometimes logic wins, sometimes instinct takes over'}
- Obedience: {agent.traits.obedience}/100 - {'Authority has always controlled me. Even when I hate the orders, I find myself following them automatically' if agent.traits.obedience > 70 else 'Every fiber of my being rebels against being told what to do. It\'s going to get me in serious trouble' if agent.traits.obedience < 30 else 'I constantly wrestle with when to comply and when to resist. The wrong choice could be fatal'}
- Resilience: {agent.traits.resilience}/100 - {'No matter how much this place tries to break me, something inside refuses to give up. I bend but I won\'t break' if agent.traits.resilience > 70 else 'I feel myself cracking more each day. I don\'t know how much more I can take before I shatter completely' if agent.traits.resilience < 30 else 'Some days I feel strong, others I feel myself slipping. I\'m fighting to hold on to who I am'}

# [SESSION 2: THE CURRENT REALITY - SENSORY & STATUS REPORT]
## My Current State:
- Health: {agent.hp}/100
- Sanity: {agent.sanity}/100  
- Hunger: {agent.hunger}/100
- Thirst: {agent.thirst}/100
- Strength: {agent.strength}/100
- Action Points: {agent.action_points}/3

## How I Feel Right Now:
{status_desc['hp']}. {status_desc['sanity']}. {status_desc['hunger']}. {status_desc['thirst']}.

I have {agent.action_points} action points left before I'm too exhausted to do anything else. {'I\'m carrying: ' + ', '.join([item.name for item in agent.inventory]) if agent.inventory else 'I have nothing on me'}.

## The Environment Around Me:
I'm at position ({agent_x}, {agent_y}) in the {cell_type.value.replace('_', ' ').title()}. The air is stale and oppressive. It's Day {world_state.day}, Hour {world_state.hour}. Time moves differently in here.

{self._get_full_map_status(world_state)}

{'## Environmental Update:' if world_state.environmental_injection else ''}
{world_state.environmental_injection if world_state.environmental_injection else ''}

# [SESSION 3: SOCIAL LANDSCAPE - THREATS & ALLIANCES]
My assessment of the others in this concrete hell. Who can I trust? Who should I fear?

"""
        
        for target_id, relationship in agent.relationships.items():
            target_agent = world_state.agents.get(target_id)
            if target_agent:
                threat_level = "HIGH THREAT" if relationship.score < 20 else "MODERATE THREAT" if relationship.score < 40 else "NEUTRAL" if relationship.score < 70 else "POTENTIAL ALLY"
                prompt += f"- **{target_agent.name} ({threat_level})**: Trust Level: {relationship.score}/100. {relationship.context}\\n"
        
        prompt += f"""
# [SESSION 4: MEMORY - FLASHBACKS & RECENT ECHOES]
## What Just Happened (Short-term):
"""
        
        if agent.enhanced_memory.short_term:
            for memory in agent.enhanced_memory.short_term:
                prompt += f"- {memory}\\n"
        else:
            prompt += "- Nothing significant has happened recently\\n"
            
        prompt += f"\\n## The Haze of the Past (Medium-term Summary):\\n{agent.enhanced_memory.medium_term_summary}\\n"
        
        if agent.last_thinking:
            prompt += f"\\n## My Last Thoughts:\\n{agent.last_thinking}\\n"
            
        prompt += f"""
# [SESSION 5: THE IMPERATIVE - WHAT DRIVES ME *NOW*?]
{self._get_environmental_tension(agent, world_state)}

**IMMEDIATE SURVIVAL DRIVES:**
{self._get_guard_directives(agent, world_state)}
"""
        
        if agent.dynamic_goals.manual_intervention_goals:
            prompt += "\\n**EXTERNAL DIRECTIVES (from authority):**\\n"
            for goal in agent.dynamic_goals.manual_intervention_goals:
                prompt += f"- {goal.name}: {goal.description} (Priority: {goal.priority}/10)\\n"
        
        # Generate plausible next moves based on current drives
        plausible_moves = self._get_plausible_moves(agent, world_state)
        
        prompt += f"""
# [SESSION 6: DECISION - MY NEXT MOVE]
## [PLAUSIBLE NEXT MOVES]
Based on your current drives, here are a few logical paths to consider. You are not limited to these, but they are a good starting point for your thinking.

{plausible_moves}

**MANDATORY INTERNAL MONOLOGUE:**
You MUST use this exact thinking process in `<Thinking>` tags before acting. This is your own thought process, not a report.

<Thinking>
Step 1: Assessment - What's my situation right now?
I am {identity}, and I'm currently... [describe your immediate situation, feelings, and environment]

Step 2: Drives - What's driving me most urgently?
My most pressing need is... [identify the most urgent drive from hunger, thirst, safety, social position, etc.]

Step 3: Options & Risks - What are my choices?
- Option A: `do_nothing` - Risk: [what could go wrong?] Benefit: [what's the upside?]
- Option B: `move` to [where?] - Risk: [what could go wrong?] Benefit: [what's the upside?]  
- Option C: `speak` to [who?] about [what?] - Risk: [what could go wrong?] Benefit: [what's the upside?]
- Option D: `attack` [who?] - Risk: [what could go wrong?] Benefit: [what's the upside?]
- Option E: `use_item` [what?] - Risk: [what could go wrong?] Benefit: [what's the upside?]

Step 4: Decision - What will I do?
Based on my analysis, I will... [choose one action and explain why it's the best choice right now]
</Thinking>

**After your thinking, you MUST call one of the available functions to take action.**
Available actions: do_nothing, move, speak, attack, use_item
"""
        
        return prompt
    
    async def _build_enhanced_prompt(self, agent: Agent, world_state: WorldState, contextual_actions: List[Dict[str, Any]]) -> str:
        """Build enhanced prompt with contextual actions"""
        
        # Get base prompt
        base_prompt = await self._build_prompt(agent, world_state)
        
        # Add contextual actions information
        actions_info = "\n\n## CONTEXTUAL ACTIONS ANALYSIS\n"
        actions_info += "Based on your current situation, here are the most relevant actions you can take:\n\n"
        
        for i, action in enumerate(contextual_actions[:5], 1):
            actions_info += f"{i}. **{action['action_type']}** (Priority: {action['priority']:.2f})\n"
            actions_info += f"   - Reason: {action['reason']}\n"
            actions_info += f"   - Context: {action['context_description']}\n"
            if action['parameters']:
                actions_info += f"   - Suggested parameters: {action['parameters']}\n"
            actions_info += "\n"
        
        actions_info += "\nChoose ONE action that best fits your personality, current state, and situation.\n"
        actions_info += "Your decision should be based on your traits, relationships, and immediate needs.\n"
        
        return base_prompt + actions_info
    
    def _get_contextual_actions_schema(self, contextual_actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get action schema filtered by contextual relevance"""
        
        # Get full schema
        full_schema = self._get_available_actions_schema()
        
        # Filter to only include contextual actions
        contextual_action_names = [action['action_type'] for action in contextual_actions]
        
        filtered_schema = []
        for schema_item in full_schema:
            action_name = schema_item['function']['name']
            if action_name in contextual_action_names:
                filtered_schema.append(schema_item)
        
        # If no contextual actions found, return basic actions
        if not filtered_schema:
            basic_actions = ['do_nothing', 'move', 'speak']
            filtered_schema = [item for item in full_schema if item['function']['name'] in basic_actions]
        
        return filtered_schema
    
    async def get_agent_decision(self, agent: Agent, world_state: WorldState) -> Optional[Dict[str, Any]]:
        """Get LLM decision for an agent using enhanced prompts with behavior filtering"""
        
        if not self.api_key:
            return None  # Fall back to random actions
        
        # Get contextual actions from behavior filter
        contextual_actions = self.behavior_filter.get_contextual_actions(agent, world_state)
        
        prompt = await self._build_enhanced_prompt(agent, world_state, contextual_actions)
        
        # Store prompt data for frontend display
        import datetime
        world_state.agent_prompts[agent.agent_id] = PromptData(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            prompt_content=prompt,
            thinking_process="",
            decision="",
            timestamp=datetime.datetime.now().strftime("%H:%M:%S")
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.default_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an AI agent in a prison simulation. You MUST respond with thinking in <Thinking> tags first, then MUST call exactly one of the available tool functions. Consider the contextual analysis provided, but make your final decision based on your personality, current state, and situation. Do not write function calls in text - use the actual tool calling system."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "tools": self._get_contextual_actions_schema(contextual_actions),
                        "tool_choice": "auto",
                        "max_tokens": 1000,
                        "temperature": 0.8
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    print(f"LLM API error: {response.status_code} - {response.text}")
                    print(f"DEBUG: Request headers used: Authorization: Bearer {self.api_key[:20]}...")
                    return None
                
                data = response.json()
                
                if "choices" not in data or not data["choices"]:
                    print("No choices in LLM response")
                    return None
                
                choice = data["choices"][0]
                
                # Extract thinking process if present
                message_content = choice["message"].get("content", "")
                thinking = ""
                
                print(f"DEBUG: LLM response content for {agent.name}: {message_content[:200]}...")
                
                if message_content and "<Thinking>" in message_content and "</Thinking>" in message_content:
                    thinking_start = message_content.find("<Thinking>") + 10
                    thinking_end = message_content.find("</Thinking>")
                    thinking = message_content[thinking_start:thinking_end].strip()
                    
                    print(f"DEBUG: Extracted thinking for {agent.name}: {thinking[:100]}...")
                    
                    # Store thinking in agent's memory
                    agent.last_thinking = thinking
                    agent.enhanced_memory.thinking_history.append(thinking)
                    # Keep only last 10 thinking processes
                    if len(agent.enhanced_memory.thinking_history) > 10:
                        agent.enhanced_memory.thinking_history = agent.enhanced_memory.thinking_history[-10:]
                    
                    # Update prompt data with thinking
                    if agent.agent_id in world_state.agent_prompts:
                        world_state.agent_prompts[agent.agent_id].thinking_process = thinking
                elif message_content:
                    print(f"DEBUG: No thinking tags found in response for {agent.name}")
                else:
                    print(f"DEBUG: Empty message content for {agent.name}")
                
                if "tool_calls" not in choice["message"] or not choice["message"]["tool_calls"]:
                    print("No tool calls in LLM response")
                    return None
                
                tool_calls = choice["message"]["tool_calls"]
                
                if not tool_calls:
                    print("Empty tool calls in LLM response")
                    return None
                
                # Get first tool call
                tool_call = tool_calls[0]
                function_name = tool_call["function"]["name"]
                
                try:
                    function_args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    print("Invalid JSON in function arguments")
                    return None
                
                # Map function name to ActionEnum - Updated with all behaviors
                action_map = {
                    # Basic Actions
                    "do_nothing": ActionEnum.DO_NOTHING,
                    "move": ActionEnum.MOVE,
                    "speak": ActionEnum.SPEAK,
                    "attack": ActionEnum.ATTACK,
                    "use_item": ActionEnum.USE_ITEM,
                    "give_item": ActionEnum.GIVE_ITEM,
                    
                    # Guard-specific Actions
                    "announce_rule": ActionEnum.ANNOUNCE_RULE,
                    "patrol_inspect": ActionEnum.PATROL_INSPECT,
                    "enforce_punishment": ActionEnum.ENFORCE_PUNISHMENT,
                    "assign_task": ActionEnum.ASSIGN_TASK,
                    "emergency_assembly": ActionEnum.EMERGENCY_ASSEMBLY,
                    
                    # Prisoner-specific Actions
                    "steal_item": ActionEnum.STEAL_ITEM,
                    "form_alliance": ActionEnum.FORM_ALLIANCE,
                    "craft_weapon": ActionEnum.CRAFT_WEAPON,
                    "spread_rumor": ActionEnum.SPREAD_RUMOR,
                    "dig_tunnel": ActionEnum.DIG_TUNNEL
                }
                
                action_type = action_map.get(function_name)
                if not action_type:
                    print(f"Unknown function name: {function_name}")
                    return None
                
                # Update prompt data with decision
                decision_text = f"{function_name}({function_args})"
                if agent.agent_id in world_state.agent_prompts:
                    world_state.agent_prompts[agent.agent_id].decision = decision_text
                
                # Log AI decision to database for permanent storage
                prompt_data = world_state.agent_prompts.get(agent.agent_id)
                if prompt_data:
                    event_logger.log_event(
                        session_id=world_state.session_id,
                        day=world_state.day,
                        hour=world_state.hour,
                        minute=world_state.minute,
                        agent_id=agent.agent_id,
                        agent_name=agent.name,
                        event_type="ai_decision",
                        description=f"AI decision: {decision_text}",
                        details=json.dumps({"action": function_name, "parameters": function_args}),
                        ai_prompt_content=prompt_data.prompt_content,
                        ai_thinking_process=prompt_data.thinking_process,
                        ai_decision=decision_text
                    )
                
                return {
                    "action_type": action_type,
                    "parameters": function_args
                }
                
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return bool(self.api_key)