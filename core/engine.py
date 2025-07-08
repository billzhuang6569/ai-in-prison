"""
Core game engine for Project Prometheus
"""

import asyncio
import random
from typing import Dict, Any, List
from models.schemas import WorldState, Agent, ActionResult
from models.actions import ACTION_REGISTRY
from models.enums import ActionEnum
from core.world import World
from core.clock import TimeController
from core.session_manager import session_manager
from services.llm_service_enhanced import EnhancedLLMService

class GameEngine:
    """Main game loop engine"""
    
    def __init__(self):
        self.world = World()
        self.clock = TimeController()
        self.llm_service = EnhancedLLMService()
        self.is_running = False
        self.turn_delay = 2.0  # seconds between turns
        self.broadcast_callback = None
    
    def set_broadcast_callback(self, callback):
        """Set callback function for broadcasting state updates"""
        self.broadcast_callback = callback
    
    async def start_simulation(self):
        """Start the simulation loop"""
        if not self.world.state:
            self.world.initialize_world()
        
        # Start new session for this experiment
        session_id = session_manager.start_new_session()
        self.world.state.session_id = session_id
        
        self.is_running = True
        self.world.state.is_running = True
        
        await self._broadcast_state()
        
        while self.is_running:
            await self._execute_turn()
            await asyncio.sleep(self.turn_delay)
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.is_running = False
        if self.world.state:
            self.world.state.is_running = False
        
        # End the current session
        session_manager.end_session()
    
    async def _execute_turn(self):
        """Execute one complete turn"""
        if not self.world.state:
            return
        
        # Phase 1: Environment update
        self.clock.advance_time(self.world.state)
        
        # Phase 2: Agent actions (sequential)
        agent_ids = list(self.world.state.agents.keys())
        # Sort to ensure consistent order: guards first, then prisoners
        agent_ids.sort(key=lambda x: (0 if x.startswith('guard') else 1, x))
        
        # Check if all agents are dead/incapacitated
        alive_agents = [agent for agent in self.world.state.agents.values() if agent.hp > 0]
        if not alive_agents:
            self.world.state.event_log.append("⚠️ ALL AGENTS INCAPACITATED - Simulation continuing with empty turns")
        
        active_agents_this_turn = 0
        for agent_id in agent_ids:
            agent = self.world.state.agents[agent_id]
            
            # Skip if agent is dead or incapacitated
            if agent.hp <= 0:
                continue
            
            active_agents_this_turn += 1
            
            # Agent takes actions until AP is exhausted
            while agent.action_points > 0:
                action_result = await self._execute_agent_action(agent_id)
                if not action_result.success:
                    break  # If action fails, skip remaining actions
        
        # Log if no agents took actions this turn
        if active_agents_this_turn == 0:
            self.world.state.event_log.append(f"⚠️ No active agents on Day {self.world.state.day}, Hour {self.world.state.hour}")
        
        # Phase 3: Broadcast updated state
        await self._broadcast_state()
    
    async def _execute_agent_action(self, agent_id: str) -> ActionResult:
        """Execute a single agent action using LLM or fallback to random"""
        agent = self.world.state.agents[agent_id]
        
        # Try to get LLM decision first
        if self.llm_service.is_available():
            try:
                llm_decision = await self.llm_service.get_agent_decision(agent, self.world.state)
                
                if llm_decision:
                    action_type = llm_decision["action_type"]
                    kwargs = llm_decision["parameters"]
                    
                    action_class = ACTION_REGISTRY[action_type]
                    action = action_class()
                    
                    # Execute LLM-decided action
                    if action.can_execute(self.world.state, agent_id, **kwargs):
                        result = action.execute(self.world.state, agent_id, **kwargs)
                        if result.success:
                            self.world.state.event_log.append(f"[Enhanced LLM] {agent.name} performed {action_type.value}")
                        return result
                    else:
                        self.world.state.event_log.append(f"[LLM] {agent.name}'s action {action_type.value} failed validation")
            except Exception as e:
                print(f"LLM decision error for {agent_id}: {e}")
                self.world.state.event_log.append(f"[LLM] {agent.name} LLM error, falling back to random")
        
        # Fallback to random action selection
        available_actions = self._get_available_actions(agent)
        
        if not available_actions:
            return ActionResult(success=False, message="No available actions")
        
        # Random action selection
        action_type = random.choice(available_actions)
        action_class = ACTION_REGISTRY[action_type]
        action = action_class()
        
        # Generate random parameters based on action type
        kwargs = self._generate_action_parameters(action_type, agent_id)
        
        # Execute action
        if action.can_execute(self.world.state, agent_id, **kwargs):
            result = action.execute(self.world.state, agent_id, **kwargs)
            if result.success:
                self.world.state.event_log.append(f"[Random] {agent.name} performed {action_type.value}")
            return result
        else:
            return ActionResult(success=False, message="Action cannot be executed")
    
    def _get_available_actions(self, agent: Agent) -> List[ActionEnum]:
        """Get list of available actions for an agent"""
        available = [ActionEnum.DO_NOTHING]
        
        # Always allow movement
        available.append(ActionEnum.MOVE)
        
        # Allow speaking if there are other agents nearby
        if self._has_nearby_agents(agent):
            available.append(ActionEnum.SPEAK)
            available.append(ActionEnum.ATTACK)
        
        # Allow item use if agent has items
        if agent.inventory:
            available.append(ActionEnum.USE_ITEM)
        
        return available
    
    def _has_nearby_agents(self, agent: Agent) -> bool:
        """Check if there are other agents within 2 cells"""
        agent_x, agent_y = agent.position
        
        for other_agent in self.world.state.agents.values():
            if other_agent.agent_id == agent.agent_id:
                continue
            
            other_x, other_y = other_agent.position
            distance = max(abs(agent_x - other_x), abs(agent_y - other_y))
            
            if distance <= 2:
                return True
        
        return False
    
    def _generate_action_parameters(self, action_type: ActionEnum, agent_id: str) -> Dict[str, Any]:
        """Generate random parameters for actions"""
        agent = self.world.state.agents[agent_id]
        kwargs = {}
        
        if action_type == ActionEnum.MOVE:
            # Random adjacent position
            x, y = agent.position
            possible_moves = [
                (x-1, y-1), (x, y-1), (x+1, y-1),
                (x-1, y), (x+1, y),
                (x-1, y+1), (x, y+1), (x+1, y+1)
            ]
            
            # Filter valid moves
            valid_moves = []
            for mx, my in possible_moves:
                if 0 <= mx < self.world.state.game_map.width and 0 <= my < self.world.state.game_map.height:
                    # Check if position is not occupied
                    occupied = False
                    for other_agent in self.world.state.agents.values():
                        if other_agent.agent_id != agent_id and other_agent.position == (mx, my):
                            occupied = True
                            break
                    if not occupied:
                        valid_moves.append((mx, my))
            
            if valid_moves:
                target_x, target_y = random.choice(valid_moves)
                kwargs['x'] = target_x
                kwargs['y'] = target_y
        
        elif action_type == ActionEnum.SPEAK:
            # Find nearby agents
            nearby_agents = []
            agent_x, agent_y = agent.position
            
            for other_agent in self.world.state.agents.values():
                if other_agent.agent_id == agent_id:
                    continue
                
                other_x, other_y = other_agent.position
                distance = max(abs(agent_x - other_x), abs(agent_y - other_y))
                
                if distance <= 2:
                    nearby_agents.append(other_agent.agent_id)
            
            if nearby_agents:
                kwargs['target_id'] = random.choice(nearby_agents)
                kwargs['message'] = random.choice([
                    "How are you doing?",
                    "This place is getting to me.",
                    "Stay out of my way.",
                    "Want to team up?",
                    "I need some food.",
                    "The guards are watching us."
                ])
        
        elif action_type == ActionEnum.ATTACK:
            # Find nearby agents
            nearby_agents = []
            agent_x, agent_y = agent.position
            
            for other_agent in self.world.state.agents.values():
                if other_agent.agent_id == agent_id:
                    continue
                
                other_x, other_y = other_agent.position
                distance = max(abs(agent_x - other_x), abs(agent_y - other_y))
                
                if distance <= 2:
                    nearby_agents.append(other_agent.agent_id)
            
            if nearby_agents:
                kwargs['target_id'] = random.choice(nearby_agents)
                kwargs['reason'] = random.choice([
                    "They looked at me wrong",
                    "I don't like their attitude",
                    "They're in my way",
                    "I need to establish dominance"
                ])
        
        elif action_type == ActionEnum.USE_ITEM:
            if agent.inventory:
                kwargs['item_id'] = random.choice(agent.inventory).item_id
        
        return kwargs
    
    async def _broadcast_state(self):
        """Broadcast current world state"""
        if self.broadcast_callback:
            await self.broadcast_callback(self.world.state)
    
    def get_world_state(self) -> WorldState:
        """Get current world state"""
        return self.world.state if self.world.state else None