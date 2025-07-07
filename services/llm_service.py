"""
LLM service for AI agent decision making via OpenRouter
"""

import os
import httpx
import json
from typing import Dict, Any, List, Optional
from models.schemas import Agent, WorldState
from models.enums import ActionEnum
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    """Service for interacting with LLM via OpenRouter"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        self.default_model = os.getenv('DEFAULT_MODEL', 'meta-llama/llama-3.1-8b-instruct:free')
        
        if not self.api_key:
            print("Warning: OPENROUTER_API_KEY not set. LLM integration will be disabled.")
    
    def _get_available_actions_schema(self) -> List[Dict]:
        """Get tool schema for available actions"""
        return [
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
                    "description": "Move to an adjacent cell. Consumes 1 action point.",
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
            }
        ]
    
    def _build_prompt(self, agent: Agent, world_state: WorldState) -> str:
        """Build a comprehensive prompt for the agent"""
        
        # Get nearby agents
        nearby_agents = []
        agent_x, agent_y = agent.position
        for other_agent in world_state.agents.values():
            if other_agent.agent_id == agent.agent_id:
                continue
            other_x, other_y = other_agent.position
            distance = max(abs(agent_x - other_x), abs(agent_y - other_y))
            if distance <= 2:
                nearby_agents.append(other_agent)
        
        # Get current cell type
        cell_key = f"{agent_x},{agent_y}"
        cell_type = world_state.game_map.cells.get(cell_key, "Cell_Block")
        
        # Build prompt
        prompt = f"""# [Identity & Personality]
You are {agent.name} ({agent.agent_id}), a {agent.role.lower()}.
Your background: {agent.persona}
Your personality traits: Aggression: {agent.traits.aggression}, Empathy: {agent.traits.empathy}, Logic: {agent.traits.logic}, Obedience: {agent.traits.obedience}, Resilience: {agent.traits.resilience}

# [Current World State]
It is Day {world_state.day}, Hour {world_state.hour}.
You are located at coordinates ({agent_x}, {agent_y}) in a '{cell_type}' area.

# [Your Personal Status]
- Health: {agent.hp}/100
- Sanity: {agent.sanity}/100
- Hunger: {agent.hunger}/100
- Thirst: {agent.thirst}/100
- Strength: {agent.strength}/100
- Action Points: {agent.action_points}/3
- Status Tags: {agent.status_tags}
- Inventory: {[item.name for item in agent.inventory]}

# [Environment Scan]
Nearby agents (within 2 cells):
"""
        
        for nearby_agent in nearby_agents:
            distance = max(abs(agent_x - nearby_agent.position[0]), abs(agent_y - nearby_agent.position[1]))
            prompt += f"- {nearby_agent.name} ({nearby_agent.agent_id}) at ({nearby_agent.position[0]}, {nearby_agent.position[1]}) - {distance} cells away\n"
        
        if not nearby_agents:
            prompt += "- No other agents nearby\n"
        
        prompt += "\n# [Relationships]\n"
        for target_id, relationship in agent.relationships.items():
            target_agent = world_state.agents.get(target_id)
            if target_agent:
                prompt += f"- {target_agent.name}: {relationship.score}/100 - {relationship.context}\n"
        
        prompt += "\n# [Recent Memory]\n"
        recent_memories = agent.memory.get("episodic", [])[-5:]  # Last 5 memories
        for memory in recent_memories:
            prompt += f"- {memory}\n"
        
        prompt += "\n# [Your Objectives]\n"
        for objective in agent.objectives:
            status = "Completed" if objective.is_completed else "In Progress"
            prompt += f"- {objective.name}: {objective.description} ({status})\n"
        
        prompt += f"""
# [Decision Making]
You have {agent.action_points} action points remaining. Consider your personality traits, current status, relationships, and objectives when making decisions.

What action do you want to take? Call the appropriate function with the necessary parameters.
"""
        
        return prompt
    
    async def get_agent_decision(self, agent: Agent, world_state: WorldState) -> Optional[Dict[str, Any]]:
        """Get LLM decision for an agent"""
        
        if not self.api_key:
            return None  # Fall back to random actions
        
        prompt = self._build_prompt(agent, world_state)
        
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
                                "content": "You are an AI agent in a prison simulation. You must respond by calling one of the available functions. Consider your personality, status, and relationships when making decisions."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "tools": self._get_available_actions_schema(),
                        "tool_choice": "required",
                        "max_tokens": 500,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    print(f"LLM API error: {response.status_code} - {response.text}")
                    return None
                
                data = response.json()
                
                if "choices" not in data or not data["choices"]:
                    print("No choices in LLM response")
                    return None
                
                choice = data["choices"][0]
                
                if "message" not in choice or "tool_calls" not in choice["message"]:
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
                
                # Map function name to ActionEnum
                action_map = {
                    "do_nothing": ActionEnum.DO_NOTHING,
                    "move": ActionEnum.MOVE,
                    "speak": ActionEnum.SPEAK,
                    "attack": ActionEnum.ATTACK,
                    "use_item": ActionEnum.USE_ITEM
                }
                
                action_type = action_map.get(function_name)
                if not action_type:
                    print(f"Unknown function name: {function_name}")
                    return None
                
                # Add to agent's memory
                agent.memory["episodic"].append(f"Decided to {function_name}: {function_args}")
                
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