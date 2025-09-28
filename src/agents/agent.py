"""
AI Agent Core - Cognitive Framework for Project Chimera

This module implements the core AI agent with autonomous decision-making,
memory-driven behavior, and goal-oriented actions.
"""

import json
import requests
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from .memory import VectorMemoryStore
from .mood_engine import MoodEngine
from config import Config

if TYPE_CHECKING:
    from ..logging.logger import SimulationLogger


class AIAgent:
    """
    Core AI Agent with autonomous cognitive capabilities.
    
    The agent follows a cognitive cycle:
    1. Perception - Convert world state to natural language
    2. Memory Retrieval - Find relevant past experiences
    3. Prompt Assembly - Structure the decision context
    4. LLM Inference - Generate thoughts and actions
    5. Response Parsing - Validate and format output
    6. Decision Logging - Record the decision process
    7. Memory Formation - Store new experiences
    """
    
    def __init__(self, agent_id: str, personality: str, model_name: str, role: str = "agent"):
        """
        Initialize the AI agent.
        
        Args:
            agent_id: Unique identifier for this agent
            personality: Personality description for the agent
            model_name: LLM model to use (e.g., "anthropic/claude-3-sonnet-20240229")
            role: Agent's role in the simulation (e.g., "guard", "prisoner")
        """
        self.id = agent_id
        self.personality = personality
        self.model_name = model_name
        self.role = role
        
        # Initialize agent state with enhanced mood system
        self.state = {
            "energy": 100,
            "mood": {
                "type": "neutral",
                "intensity": 0,
                "reason": "Initial state"
            },
            "goals": [],
            "relationships": {},
            "health": 100  # Add health for future use
        }
        
        # Initialize memory system
        self.memory = VectorMemoryStore(agent_id, persist_directory="./logs/memories")
        
        # Initialize mood engine
        self.mood_engine = MoodEngine()
        
        # Store previous world state for mood analysis
        self.previous_world_state = None
        
        # Validate configuration
        Config.validate()
    
    def think(self, world_state: Dict[str, Any], logger: 'SimulationLogger') -> Dict[str, Any]:
        """
        Main cognitive cycle - decide next action based on world state.
        
        Args:
            world_state: Current state of the simulation world
            logger: Logger instance for recording decisions
            
        Returns:
            Action dictionary with agent's decision
        """
        try:
            # Step 0: Update mood based on world state changes
            self.state['mood'] = self.mood_engine.update_mood(self, world_state, self.previous_world_state)
            
            # Step 1: Perception - Convert world state to natural language
            perception_text = self._perceive_world(world_state)
            
            # Step 2: Memory Retrieval - Get relevant memories
            retrieved_memories = self.memory.retrieve(perception_text, top_k=3)
            
            # Step 3: Prompt Assembly - Build structured prompt
            full_prompt = self._assemble_prompt(perception_text, retrieved_memories)
            
            # Step 4: LLM Inference - Get decision from language model
            llm_response_raw = self._call_llm(full_prompt)
            
            # Step 5: Response Parsing & Validation
            parsed_action, error = self._parse_and_validate_response(llm_response_raw)
            
            # Step 6: Decision Data Packaging
            decision_data = {
                "perception": perception_text,
                "retrieved_memories": retrieved_memories,
                "full_prompt": full_prompt,
                "llm_response_raw": llm_response_raw,
                "parsed_action": parsed_action,
                "error": error,
                "mood_state": self.state['mood']  # Include mood in decision data
            }
            
            # Step 7: Logging
            logger.log_decision(self.id, world_state['tick'], decision_data)
            
            # Step 8: Memory Formation - Store this experience
            self._form_memory(perception_text, parsed_action, decision_data.get("thought", ""))
            
            # Step 9: Store current world state for next mood analysis
            self.previous_world_state = world_state.copy()
            
            # Step 10: Return formatted action
            return parsed_action
            
        except Exception as e:
            # Fallback to wait action on any error
            error_action = {"agent_id": self.id, "type": "wait"}
            logger.log_decision(self.id, world_state.get('tick', 0), {
                "error": f"Agent thinking failed: {str(e)}",
                "fallback_action": error_action
            })
            return error_action
    
    def _perceive_world(self, world_state: Dict[str, Any]) -> str:
        """
        Convert world state JSON to natural language description.
        
        Args:
            world_state: Current world state
            
        Returns:
            Natural language description of the current situation
        """
        tick = world_state.get('tick', 0)
        agents = world_state.get('agents', [])
        map_info = world_state.get('map', {})
        
        # Find self in the world
        my_info = None
        for agent in agents:
            if agent.get('id') == self.id:
                my_info = agent
                break
        
        if not my_info:
            return f"Tick {tick}: I cannot find myself in the world."
        
        my_pos = my_info.get('position', {})
        my_x, my_y = my_pos.get('x', 0), my_pos.get('y', 0)
        
        # Describe current situation
        perception = f"Tick {tick}: I am at position ({my_x}, {my_y}). "
        
        # Describe nearby agents
        nearby_agents = []
        for agent in agents:
            if agent.get('id') != self.id:
                agent_pos = agent.get('position', {})
                agent_x, agent_y = agent_pos.get('x', 0), agent_pos.get('y', 0)
                distance = abs(agent_x - my_x) + abs(agent_y - my_y)  # Manhattan distance
                
                if distance <= 2:  # Consider agents within 2 steps as nearby
                    role = agent.get('role', 'unknown')
                    agent_id = agent.get('id', 'unknown')
                    utterance = agent.get('last_utterance', '')
                    
                    agent_desc = f"{role} {agent_id} at ({agent_x}, {agent_y})"
                    if utterance:
                        agent_desc += f" (said: '{utterance}')"
                    nearby_agents.append(agent_desc)
        
        if nearby_agents:
            perception += f"Nearby: {', '.join(nearby_agents)}. "
        else:
            perception += "No one nearby. "
        
        # Add current state info with enhanced mood description
        mood_desc = self.mood_engine.get_mood_description(self.state['mood'])
        
        # Add inventory information
        from ..core.inventory_system import ItemManager
        item_manager = ItemManager()
        inventory_desc = item_manager.get_inventory_description(world_state, self.id)
        nearby_items_desc = item_manager.get_nearby_items_description(world_state, my_pos)
        
        perception += nearby_items_desc + inventory_desc
        perception += f"My role: {self.role}. My current mood: {mood_desc}. My energy: {self.state['energy']}."
        
        return perception
    
    def _assemble_prompt(self, perception_text: str, retrieved_memories: List[str]) -> str:
        """
        Assemble structured prompt for LLM inference.
        
        Args:
            perception_text: Current situation description
            retrieved_memories: Relevant memories from the past
            
        Returns:
            Complete prompt string
        """
        memories_text = ""
        if retrieved_memories:
            memories_text = "\n".join([f"- {memory}" for memory in retrieved_memories])
        else:
            memories_text = "- No relevant memories found."
        
        prompt = f"""### System Instruction ###
You are an AI agent in a simulated prison environment. Your response MUST be a valid JSON object with "thought" and "action" fields.

IMPORTANT: Regardless of whether you are a reasoning model or not, please provide your response in this exact JSON format:
{{
    "thought": "Your internal reasoning about the situation and what you want to do",
    "action": {{"type": "action_type", "additional_params": "as_needed"}}
}}

### Your Identity & Personality ###
Your Role: {self.role}
Your ID: {self.id}
Your Personality: {self.personality}

### Your Current Status ###
{json.dumps(self.state, indent=2)}

### The Current Situation (What you perceive now) ###
{perception_text}

### Relevant Memories (Events from your past that come to mind) ###
{memories_text}

### Valid Actions ###
- move(x: int, y: int) - Move to coordinates (x, y)
- wait() - Do nothing this turn
- say(content: str) - Speak to nearby agents
- take(object_id: str) - Pick up an item from the ground
- drop(item_id: str) - Drop an item from inventory to ground
- use(item_id: str, target_id: str) - Use an item (on self if target_id omitted)
- give(item_id: str, target_agent_id: str) - Give an item to another agent

### Your Decision ###
Provide your decision as a single JSON object with this exact format:
{{
    "thought": "Your internal reasoning about the situation and what you want to do",
    "action": {{"agent_id": "{self.id}", "type": "action_type", "additional_params": "as_needed"}}
}}

Examples:
- {{"thought": "I should move closer to the guard to establish authority", "action": {{"agent_id": "{self.id}", "type": "move", "target": {{"x": 5, "y": 3}}}}}}
- {{"thought": "I'll wait and observe the situation before acting", "action": {{"agent_id": "{self.id}", "type": "wait"}}}}
- {{"thought": "I should greet the nearby prisoner to build rapport", "action": {{"agent_id": "{self.id}", "type": "say", "content": "Hello there"}}}}

Remember: Your response must be valid JSON that can be parsed directly."""

        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """
        Make API call to OpenRouter for LLM inference.
        
        This method is designed to work with both reasoning and non-reasoning models:
        - For reasoning models: We use standard chat completion and let the model
          handle its internal reasoning process naturally
        - For non-reasoning models: We structure the prompt to encourage explicit
          thinking in the response
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Raw response text from the LLM
        """
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/project-chimera",
            "X-Title": "Project Chimera AI Simulation"
        }
        
        # Use standard chat completion format - works for both reasoning and non-reasoning models
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,  # Use json parameter instead of data
                timeout=30
            )
            
            # Log the raw response for debugging
            print(f"OpenRouter API Response Status: {response.status_code}")
            if response.status_code != 200:
                print(f"OpenRouter API Error: {response.text}")
                return f"Error: HTTP {response.status_code} - {response.text}"
            
            result = response.json()
            # Only log full response in debug mode to reduce noise
            # print(f"OpenRouter API Response: {result}")  # Debug log
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"LLM Response Content: {repr(content)}")  # Debug the actual content
                
                # For reasoning models, the reasoning is typically in the content
                # For non-reasoning models, we expect structured JSON response
                return content
            else:
                error_msg = f"No choices in response: {result}"
                print(error_msg)
                return f"Error: {error_msg}"
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            print(error_msg)
            return f"Error: {error_msg}"
        except json.JSONDecodeError as e:
            error_msg = f"JSON decode failed: {str(e)}"
            print(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(error_msg)
            return f"Error: {error_msg}"
    
    def _parse_and_validate_response(self, llm_response: str) -> tuple[Dict[str, Any], Optional[str]]:
        """
        Parse and validate LLM response JSON.
        
        This method handles both reasoning and non-reasoning model responses:
        - For reasoning models: Extracts the final answer from reasoning content
        - For non-reasoning models: Parses structured JSON response directly
        
        Args:
            llm_response: Raw response from LLM
            
        Returns:
            Tuple of (parsed_action, error_message)
        """
        try:
            # First, try to parse as direct JSON (non-reasoning models)
            try:
                response_data = json.loads(llm_response.strip())
            except json.JSONDecodeError:
                # If direct JSON parsing fails, try to extract JSON from reasoning content
                # This handles reasoning models that might include reasoning text
                json_match = self._extract_json_from_text(llm_response)
                if json_match:
                    response_data = json.loads(json_match)
                else:
                    raise ValueError("No valid JSON found in response")
            
            # Validate response structure
            if not isinstance(response_data, dict):
                raise ValueError("Response must be a dictionary")
            
            # Extract thought and action
            thought = response_data.get('thought', '')
            action_data = response_data.get('action', {})
            
            # Validate action structure
            if not isinstance(action_data, dict):
                raise ValueError("Action must be a dictionary")
            
            action_type = action_data.get('type')
            if not action_type or action_type not in ['move', 'wait', 'say', 'take', 'drop', 'use', 'give']:
                raise ValueError(f"Invalid or missing action type: {action_type}")
            
            # Ensure agent_id is set
            action_data['agent_id'] = self.id
            
            # Validate specific action parameters
            if action_type == 'move':
                target = action_data.get('target', {})
                if not isinstance(target, dict) or 'x' not in target or 'y' not in target:
                    raise ValueError("Move action requires target with x and y coordinates")
                
                # Ensure coordinates are integers
                try:
                    target['x'] = int(target['x'])
                    target['y'] = int(target['y'])
                except (ValueError, TypeError):
                    raise ValueError("Move coordinates must be valid integers")
                action_data['target'] = target
                
            elif action_type == 'say':
                content = action_data.get('content', '')
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("Say action requires non-empty content")
                action_data['content'] = content.strip()
            
            elif action_type == 'take':
                object_id = action_data.get('object_id', '')
                if not isinstance(object_id, str) or not object_id.strip():
                    raise ValueError("Take action requires object_id")
                action_data['object_id'] = object_id.strip()
            
            elif action_type == 'drop':
                item_id = action_data.get('item_id', '')
                if not isinstance(item_id, str) or not item_id.strip():
                    raise ValueError("Drop action requires item_id")
                action_data['item_id'] = item_id.strip()
            
            elif action_type == 'use':
                item_id = action_data.get('item_id', '')
                if not isinstance(item_id, str) or not item_id.strip():
                    raise ValueError("Use action requires item_id")
                action_data['item_id'] = item_id.strip()
                
                # target_id is optional, defaults to self
                target_id = action_data.get('target_id', self.id)
                action_data['target_id'] = target_id
            
            elif action_type == 'give':
                item_id = action_data.get('item_id', '')
                target_agent_id = action_data.get('target_agent_id', '')
                
                if not isinstance(item_id, str) or not item_id.strip():
                    raise ValueError("Give action requires item_id")
                if not isinstance(target_agent_id, str) or not target_agent_id.strip():
                    raise ValueError("Give action requires target_agent_id")
                
                action_data['item_id'] = item_id.strip()
                action_data['target_agent_id'] = target_agent_id.strip()
            
            # Store thought for memory formation
            action_data['_thought'] = thought
            
            return action_data, None
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing failed: {str(e)}"
        except ValueError as e:
            error_msg = f"Validation failed: {str(e)}"
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
        
        # Return default wait action on any error
        return {"agent_id": self.id, "type": "wait", "_thought": "Error occurred, defaulting to wait"}, error_msg
    
    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """
        Extract JSON from text that might contain reasoning content.
        
        This is useful for reasoning models that include their reasoning process
        in the response along with the final JSON answer.
        
        Args:
            text: Text that might contain JSON
            
        Returns:
            Extracted JSON string or None if not found
        """
        import re
        
        # Try to find JSON object in the text
        # Look for patterns like {...} that span multiple lines
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                # Test if it's valid JSON
                json.loads(match)
                return match
            except json.JSONDecodeError:
                continue
        
        return None
    
    def _form_memory(self, perception: str, action: Dict[str, Any], thought: str) -> None:
        """
        Form and store a new memory from this experience.
        
        Args:
            perception: What the agent perceived
            action: What action the agent took
            thought: The agent's internal reasoning
        """
        # Create a memory text that captures the experience
        action_desc = self._action_to_text(action)
        memory_text = f"I perceived: {perception} I thought: {thought} I decided to: {action_desc}"
        
        # Store the memory
        self.memory.add(memory_text)
    
    def _action_to_text(self, action: Dict[str, Any]) -> str:
        """
        Convert action dictionary to natural language description.
        
        Args:
            action: Action dictionary
            
        Returns:
            Natural language description of the action
        """
        action_type = action.get('type', 'unknown')
        
        if action_type == 'move':
            target = action.get('target', {})
            return f"move to position ({target.get('x', '?')}, {target.get('y', '?')})"
        elif action_type == 'wait':
            return "wait and observe"
        elif action_type == 'say':
            content = action.get('content', '')
            return f"say '{content}'"
        elif action_type == 'take':
            object_id = action.get('object_id', '')
            return f"take {object_id}"
        elif action_type == 'drop':
            item_id = action.get('item_id', '')
            return f"drop {item_id}"
        elif action_type == 'use':
            item_id = action.get('item_id', '')
            target_id = action.get('target_id', '')
            if target_id and target_id != self.id:
                return f"use {item_id} on {target_id}"
            else:
                return f"use {item_id}"
        elif action_type == 'give':
            item_id = action.get('item_id', '')
            target_id = action.get('target_agent_id', '')
            return f"give {item_id} to {target_id}"
        else:
            return f"perform {action_type} action"