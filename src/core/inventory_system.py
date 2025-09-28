"""
Inventory and Item System for Project Chimera

This module manages items, inventories, and item-related behaviors in the simulation.
"""

import uuid
from typing import Dict, List, Any, Optional


class ItemManager:
    """
    Manages items and their properties in the simulation world.
    """
    
    def __init__(self):
        """Initialize the item manager with predefined item types."""
        self.item_templates = {
            "Food": {
                "name": "Food Ration",
                "properties": {"energy_boost": 30},
                "consumable": True,
                "description": "A basic food ration that restores energy"
            },
            "Readable": {
                "name": "Crumpled Note",
                "properties": {"content": "Secret message"},
                "consumable": False,
                "description": "A piece of paper with writing on it"
            },
            "Key": {
                "name": "Key Card",
                "properties": {"access_level": "A"},
                "consumable": False,
                "description": "A key card that opens certain doors"
            },
            "Weapon": {
                "name": "Makeshift Shiv",
                "properties": {"damage": 10},
                "consumable": False,
                "description": "A crude weapon made from available materials"
            },
            "Consumable": {
                "name": "Medkit",
                "properties": {"health_boost": 40},
                "consumable": True,
                "description": "Medical supplies for treating injuries"
            }
        }
    
    def create_item(self, item_type: str, position: Optional[Dict[str, int]] = None, 
                   custom_properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new item instance.
        
        Args:
            item_type: Type of item to create
            position: Position in the world (None if in inventory)
            custom_properties: Custom properties to override defaults
            
        Returns:
            Item dictionary
        """
        if item_type not in self.item_templates:
            raise ValueError(f"Unknown item type: {item_type}")
        
        template = self.item_templates[item_type].copy()
        item_id = f"{item_type.lower()}_{str(uuid.uuid4())[:8]}"
        
        # Merge custom properties
        if custom_properties:
            template["properties"].update(custom_properties)
        
        return {
            "id": item_id,
            "type": item_type,
            "name": template["name"],
            "position": position,
            "properties": template["properties"],
            "consumable": template["consumable"],
            "description": template["description"]
        }
    
    def get_items_at_position(self, world_state: Dict[str, Any], x: int, y: int) -> List[Dict[str, Any]]:
        """Get all items at a specific position."""
        items = []
        for item in world_state.get('objects', []):
            item_pos = item.get('position')
            if item_pos and item_pos.get('x') == x and item_pos.get('y') == y:
                items.append(item)
        return items
    
    def get_agent_inventory_items(self, world_state: Dict[str, Any], agent_id: str) -> List[Dict[str, Any]]:
        """Get all items in an agent's inventory."""
        # Find agent
        agent = None
        for a in world_state.get('agents', []):
            if a.get('id') == agent_id:
                agent = a
                break
        
        if not agent:
            return []
        
        inventory_ids = agent.get('inventory', [])
        items = []
        
        for item in world_state.get('objects', []):
            if item.get('id') in inventory_ids:
                items.append(item)
        
        return items
    
    def find_item_by_id(self, world_state: Dict[str, Any], item_id: str) -> Optional[Dict[str, Any]]:
        """Find an item by its ID."""
        for item in world_state.get('objects', []):
            if item.get('id') == item_id:
                return item
        return None
    
    def use_item(self, item: Dict[str, Any], target_agent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply item effects to a target agent.
        
        Args:
            item: Item to use
            target_agent: Agent to apply effects to
            
        Returns:
            Updated agent state
        """
        properties = item.get('properties', {})
        
        # Apply energy boost
        if 'energy_boost' in properties:
            current_energy = target_agent.get('status', {}).get('energy', 100)
            new_energy = min(100, current_energy + properties['energy_boost'])
            if 'status' not in target_agent:
                target_agent['status'] = {}
            target_agent['status']['energy'] = new_energy
        
        # Apply health boost
        if 'health_boost' in properties:
            current_health = target_agent.get('status', {}).get('health', 100)
            new_health = min(100, current_health + properties['health_boost'])
            if 'status' not in target_agent:
                target_agent['status'] = {}
            target_agent['status']['health'] = new_health
        
        return target_agent
    
    def get_nearby_items_description(self, world_state: Dict[str, Any], agent_pos: Dict[str, int]) -> str:
        """Get description of items near an agent."""
        x, y = agent_pos.get('x', 0), agent_pos.get('y', 0)
        nearby_items = []
        
        # Check current position and adjacent positions
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                items = self.get_items_at_position(world_state, x + dx, y + dy)
                for item in items:
                    distance = abs(dx) + abs(dy)
                    if distance == 0:
                        nearby_items.append(f"{item['name']} here")
                    else:
                        nearby_items.append(f"{item['name']} nearby")
        
        if nearby_items:
            return f"Items visible: {', '.join(nearby_items)}. "
        else:
            return "No items visible. "
    
    def get_inventory_description(self, world_state: Dict[str, Any], agent_id: str) -> str:
        """Get description of agent's inventory."""
        items = self.get_agent_inventory_items(world_state, agent_id)
        
        if not items:
            return "Inventory: empty. "
        
        item_names = [item['name'] for item in items]
        return f"Inventory: {', '.join(item_names)}. "