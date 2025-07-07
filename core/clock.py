"""
Time management system for Project Prometheus
"""

from models.schemas import WorldState
import json

class TimeController:
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self):
        with open('configs/game_rules.json', 'r') as f:
            return json.load(f)
    
    def advance_time(self, world_state: WorldState):
        """Advance time by 1 hour and apply status changes"""
        world_state.hour += 1
        
        # New day
        if world_state.hour >= 24:
            world_state.hour = 0
            world_state.day += 1
            world_state.event_log.append(f"--- Day {world_state.day} begins ---")
        
        # Apply hourly status changes to all agents
        for agent in world_state.agents.values():
            self._apply_hourly_changes(agent)
    
    def _apply_hourly_changes(self, agent):
        """Apply hourly status degradation"""
        # Increase hunger and thirst
        agent.hunger = min(100, agent.hunger + self.rules["status_rules"]["hunger_increase_per_hour"])
        agent.thirst = min(100, agent.thirst + self.rules["status_rules"]["thirst_increase_per_hour"])
        
        # Apply sanity penalties
        sanity_penalty = 0
        
        # Penalty for being in solitary
        # Note: This would need position-to-cell-type mapping
        
        # Penalty for negative status tags
        negative_tags = ["hungry", "thirsty", "injured", "exhausted"]
        for tag in agent.status_tags:
            if tag.lower() in negative_tags:
                sanity_penalty += self.rules["status_rules"]["sanity_penalty_per_bad_tag"]
        
        agent.sanity = max(0, agent.sanity - sanity_penalty)
        
        # Update status tags based on current values
        self._update_status_tags(agent)
        
        # Reset action points
        agent.action_points = min(3, 3 - max(0, (100 - agent.hp) // 25))  # Reduced AP if low HP
    
    def _update_status_tags(self, agent):
        """Update status tags based on current values"""
        agent.status_tags = []
        
        if agent.hunger > 70:
            agent.status_tags.append("hungry")
        if agent.thirst > 70:
            agent.status_tags.append("thirsty")
        if agent.hp < 50:
            agent.status_tags.append("injured")
        if agent.sanity < 30:
            agent.status_tags.append("unstable")
        if agent.hp < 20:
            agent.status_tags.append("critical")