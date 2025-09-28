"""
Simulation Core Engine - World Engine for Project Chimera

This module implements the core simulation engine that manages world state
and processes agent actions in a deterministic, stateless manner.
"""

import copy
from typing import Dict, List, Any, Tuple
from .inventory_system import ItemManager


class SimulationEngine:
    """
    The core simulation engine that acts as the "physics laws" of the virtual world.
    
    This engine is designed to be:
    - Deterministic: Same input always produces same output
    - Stateless: Engine itself holds no state
    - Atomic: All actions in a tick are processed simultaneously
    """
    
    def __init__(self):
        """Initialize the simulation engine."""
        self.item_manager = ItemManager()
    
    def calculate_next_state(self, current_state: Dict[str, Any], actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate the next world state based on current state and agent actions.
        
        Args:
            current_state: The current world state dictionary
            actions: List of action dictionaries from agents
            
        Returns:
            A new world state dictionary with all changes applied
        """
        # Step 1: Create a deep copy of the current state
        new_state = copy.deepcopy(current_state)
        
        # Step 2: Conflict preprocessing - identify invalid moves
        valid_actions = self._preprocess_actions(new_state, actions)
        
        # Step 3: Process all valid actions
        for action in valid_actions:
            action_type = action.get('type')
            
            if action_type == 'move':
                self._handle_move(new_state, action)
            elif action_type == 'wait':
                self._handle_wait(new_state, action)
            elif action_type == 'say':
                self._handle_say(new_state, action)
            elif action_type == 'take':
                self._handle_take(new_state, action)
            elif action_type == 'drop':
                self._handle_drop(new_state, action)
            elif action_type == 'use':
                self._handle_use(new_state, action)
            elif action_type == 'give':
                self._handle_give(new_state, action)
            # Future action types can be added here
        
        # Step 4: Increment tick counter
        new_state['tick'] += 1
        
        return new_state
    
    def _preprocess_actions(self, state: Dict[str, Any], actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Preprocess actions to identify and filter out invalid moves.
        
        Args:
            state: Current world state
            actions: List of all actions to process
            
        Returns:
            List of valid actions after conflict resolution
        """
        valid_actions = []
        move_actions = []
        non_move_actions = []
        
        # Separate move actions from other actions
        for action in actions:
            if action.get('type') == 'move':
                move_actions.append(action)
            else:
                non_move_actions.append(action)
        
        # Check for move conflicts
        target_positions = {}
        for action in move_actions:
            target = action.get('target', {})
            target_key = (target.get('x'), target.get('y'))
            
            if target_key not in target_positions:
                target_positions[target_key] = []
            target_positions[target_key].append(action)
        
        # Only allow moves where there's no conflict (single agent per target)
        for target_key, conflicting_actions in target_positions.items():
            if len(conflicting_actions) == 1:
                action = conflicting_actions[0]
                # Additional validation for the move
                if self._is_valid_move(state, action):
                    valid_actions.append(action)
        
        # All non-move actions are valid (wait, say, etc.)
        valid_actions.extend(non_move_actions)
        
        return valid_actions
    
    def _is_valid_move(self, state: Dict[str, Any], action: Dict[str, Any]) -> bool:
        """
        Validate if a move action is legal.
        
        Args:
            state: Current world state
            action: Move action to validate
            
        Returns:
            True if move is valid, False otherwise
        """
        target = action.get('target', {})
        target_x = target.get('x')
        target_y = target.get('y')
        
        if target_x is None or target_y is None:
            return False
        
        # Check map boundaries
        map_info = state.get('map', {})
        map_size = map_info.get('size', [0, 0])
        if target_x < 0 or target_y < 0 or target_x >= map_size[0] or target_y >= map_size[1]:
            return False
        
        # Check if target position is a wall
        grid = map_info.get('grid', [])
        for cell in grid:
            if cell.get('x') == target_x and cell.get('y') == target_y:
                if cell.get('type') == 'Wall':
                    return False
        
        # Check if target position is occupied by another agent
        agents = state.get('agents', [])
        for agent in agents:
            agent_pos = agent.get('position', {})
            if agent_pos.get('x') == target_x and agent_pos.get('y') == target_y:
                # Position is occupied by another agent
                if agent.get('id') != action.get('agent_id'):
                    return False
        
        return True
    
    def _handle_move(self, state: Dict[str, Any], action: Dict[str, Any]) -> None:
        """
        Handle move action by updating agent position.
        
        Args:
            state: World state to modify
            action: Move action dictionary
        """
        agent_id = action.get('agent_id')
        target = action.get('target', {})
        
        # Find and update the agent's position
        agents = state.get('agents', [])
        for agent in agents:
            if agent.get('id') == agent_id:
                agent['position'] = {
                    'x': target.get('x'),
                    'y': target.get('y')
                }
                break
    
    def _handle_wait(self, state: Dict[str, Any], action: Dict[str, Any]) -> None:
        """
        Handle wait action (no-op).
        
        Args:
            state: World state (unchanged)
            action: Wait action dictionary
        """
        # Wait action does nothing to the state
        pass
    
    def _handle_say(self, state: Dict[str, Any], action: Dict[str, Any]) -> None:
        """
        Handle say action by updating agent's last utterance.
        
        Args:
            state: World state to modify
            action: Say action dictionary
        """
        agent_id = action.get('agent_id')
        content = action.get('content', '')
        
        # Find and update the agent's last utterance
        agents = state.get('agents', [])
        for agent in agents:
            if agent.get('id') == agent_id:
                agent['last_utterance'] = content
                break
    
    def _handle_take(self, state: Dict[str, Any], action: Dict[str, Any]) -> None:
        """Handle take action - pick up an item from the ground."""
        agent_id = action.get('agent_id')
        object_id = action.get('object_id')
        
        if not object_id:
            return
        
        # Find the agent
        agent = None
        for a in state.get('agents', []):
            if a.get('id') == agent_id:
                agent = a
                break
        
        if not agent:
            return
        
        # Find the item
        item = self.item_manager.find_item_by_id(state, object_id)
        if not item or not item.get('position'):
            return  # Item not found or already in someone's inventory
        
        # Check if agent is close enough to the item
        agent_pos = agent.get('position', {})
        item_pos = item.get('position', {})
        distance = abs(agent_pos.get('x', 0) - item_pos.get('x', 0)) + abs(agent_pos.get('y', 0) - item_pos.get('y', 0))
        
        if distance > 1:  # Must be adjacent or on same tile
            return
        
        # Move item to agent's inventory
        if 'inventory' not in agent:
            agent['inventory'] = []
        agent['inventory'].append(object_id)
        item['position'] = None  # Remove from world position
    
    def _handle_drop(self, state: Dict[str, Any], action: Dict[str, Any]) -> None:
        """Handle drop action - drop an item from inventory to ground."""
        agent_id = action.get('agent_id')
        item_id = action.get('item_id')
        
        if not item_id:
            return
        
        # Find the agent
        agent = None
        for a in state.get('agents', []):
            if a.get('id') == agent_id:
                agent = a
                break
        
        if not agent or item_id not in agent.get('inventory', []):
            return
        
        # Find the item
        item = self.item_manager.find_item_by_id(state, item_id)
        if not item:
            return
        
        # Remove from inventory and place on ground
        agent['inventory'].remove(item_id)
        agent_pos = agent.get('position', {})
        item['position'] = {'x': agent_pos.get('x', 0), 'y': agent_pos.get('y', 0)}
    
    def _handle_use(self, state: Dict[str, Any], action: Dict[str, Any]) -> None:
        """Handle use action - use an item on self or target."""
        agent_id = action.get('agent_id')
        item_id = action.get('item_id')
        target_id = action.get('target_id', agent_id)  # Default to self
        
        if not item_id:
            return
        
        # Find the agent
        agent = None
        for a in state.get('agents', []):
            if a.get('id') == agent_id:
                agent = a
                break
        
        if not agent or item_id not in agent.get('inventory', []):
            return
        
        # Find the target agent
        target_agent = None
        for a in state.get('agents', []):
            if a.get('id') == target_id:
                target_agent = a
                break
        
        if not target_agent:
            return
        
        # Check distance if using on another agent
        if target_id != agent_id:
            agent_pos = agent.get('position', {})
            target_pos = target_agent.get('position', {})
            distance = abs(agent_pos.get('x', 0) - target_pos.get('x', 0)) + abs(agent_pos.get('y', 0) - target_pos.get('y', 0))
            
            if distance > 1:  # Must be adjacent
                return
        
        # Find and use the item
        item = self.item_manager.find_item_by_id(state, item_id)
        if not item:
            return
        
        # Apply item effects
        self.item_manager.use_item(item, target_agent)
        
        # Remove consumable items after use
        if item.get('consumable', False):
            agent['inventory'].remove(item_id)
            # Remove item from world objects
            state['objects'] = [obj for obj in state.get('objects', []) if obj.get('id') != item_id]
    
    def _handle_give(self, state: Dict[str, Any], action: Dict[str, Any]) -> None:
        """Handle give action - give an item to another agent."""
        agent_id = action.get('agent_id')
        item_id = action.get('item_id')
        target_agent_id = action.get('target_agent_id')
        
        if not item_id or not target_agent_id:
            return
        
        # Find both agents
        giver = None
        receiver = None
        
        for a in state.get('agents', []):
            if a.get('id') == agent_id:
                giver = a
            elif a.get('id') == target_agent_id:
                receiver = a
        
        if not giver or not receiver or item_id not in giver.get('inventory', []):
            return
        
        # Check distance
        giver_pos = giver.get('position', {})
        receiver_pos = receiver.get('position', {})
        distance = abs(giver_pos.get('x', 0) - receiver_pos.get('x', 0)) + abs(giver_pos.get('y', 0) - receiver_pos.get('y', 0))
        
        if distance > 1:  # Must be adjacent
            return
        
        # Transfer item
        giver['inventory'].remove(item_id)
        if 'inventory' not in receiver:
            receiver['inventory'] = []
        receiver['inventory'].append(item_id)