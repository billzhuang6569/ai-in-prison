"""
Time management system for Project Prometheus
"""

from models.schemas import WorldState
from database.event_logger import event_logger
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
        
        # Apply hunger and thirst HP penalties (progressive damage algorithm)
        hp_penalty = 0
        
        # Hunger HP damage (critical after 80, severe after 90)
        if agent.hunger > 80:
            # Progressive damage: (hunger - 80)^2 / 40
            excess_hunger = agent.hunger - 80
            hunger_damage = (excess_hunger ** 2) / 40
            hp_penalty += min(15, hunger_damage)  # Cap at 15 HP per hour
        
        # Thirst HP damage (critical after 75, severe after 85)
        if agent.thirst > 75:
            # Progressive damage: (thirst - 75)^2 / 30 (thirst is more critical)
            excess_thirst = agent.thirst - 75
            thirst_damage = (excess_thirst ** 2) / 30
            hp_penalty += min(20, thirst_damage)  # Cap at 20 HP per hour
        
        # Apply HP damage
        if hp_penalty > 0:
            agent.hp = max(0, agent.hp - int(hp_penalty))
            agent.memory["episodic"].append(f"Lost {int(hp_penalty)} HP due to hunger/thirst")
        
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
        
        # Hunger status tags
        if agent.hunger > 90:
            agent.status_tags.append("starving")
        elif agent.hunger > 80:
            agent.status_tags.append("very_hungry")
        elif agent.hunger > 60:
            agent.status_tags.append("hungry")
        
        # Thirst status tags
        if agent.thirst > 85:
            agent.status_tags.append("dehydrated")
        elif agent.thirst > 75:
            agent.status_tags.append("very_thirsty")
        elif agent.thirst > 55:
            agent.status_tags.append("thirsty")
        
        # Health status tags
        if agent.hp < 20:
            agent.status_tags.append("critical")
        elif agent.hp < 40:
            agent.status_tags.append("injured")
        elif agent.hp < 60:
            agent.status_tags.append("wounded")
        
        # Mental status tags
        if agent.sanity < 20:
            agent.status_tags.append("unhinged")
        elif agent.sanity < 40:
            agent.status_tags.append("unstable")
        elif agent.sanity < 60:
            agent.status_tags.append("stressed")
        
        # Death state
        if agent.hp <= 0:
            agent.status_tags.append("deceased")
            
            # Record death event for milestones
            if world_state.session_id:
                event_logger.log_event(
                    session_id=world_state.session_id,
                    day=world_state.day,
                    hour=world_state.hour,
                    minute=world_state.minute,
                    agent_id=agent.agent_id,
                    agent_name=agent.name,
                    event_type="death",
                    description=f"{agent.name} has died from hunger, thirst, or injuries",
                    details=f'{{"hp": {agent.hp}, "hunger": {agent.hunger}, "thirst": {agent.thirst}}}'
                )
                world_state.event_log.append(f"💀 {agent.name} has died")