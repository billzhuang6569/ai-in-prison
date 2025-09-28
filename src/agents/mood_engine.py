"""
Dynamic Mood Engine for Project Chimera

This module implements a hybrid mood system that combines rule-based algorithms
for simple emotional changes with LLM-powered analysis for complex social interactions.
"""

import json
import requests
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from config import Config

if TYPE_CHECKING:
    from .agent import AIAgent


class MoodEngine:
    """
    Hybrid mood system combining rule-based algorithms with LLM cognitive analysis.
    
    Architecture:
    - Rule-Based Layer: Fast, cost-free processing of simple emotional changes
    - Cognitive Layer: LLM-powered analysis of complex social interactions
    """
    
    def __init__(self):
        """Initialize the mood engine."""
        self.emotion_types = [
            "neutral", "happy", "angry", "fearful", "sad", "excited", 
            "bored", "anxious", "satisfied", "frustrated", "exhausted"
        ]
        
        # Rule-based thresholds
        self.energy_thresholds = {
            "exhausted": 20,
            "tired": 40,
            "energetic": 80
        }
        
        # Mood decay rate per tick
        self.decay_rate = 0.95
    
    def update_mood(self, agent: 'AIAgent', world_state: Dict[str, Any], 
                   previous_world_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update agent's mood based on current situation and events.
        
        Args:
            agent: The agent whose mood to update
            world_state: Current world state
            previous_world_state: Previous world state for event detection
            
        Returns:
            Updated mood dictionary
        """
        current_mood = agent.state.get('mood', {
            "type": "neutral",
            "intensity": 0,
            "reason": "Initial state"
        })
        
        # Step 1: Mood decay (rule-based)
        current_mood = self._apply_mood_decay(current_mood)
        
        # Step 2: Physical effects (rule-based)
        current_mood = self._apply_physical_effects(agent, current_mood)
        
        # Step 3: Social events analysis (LLM-powered)
        if previous_world_state:
            social_events = self._detect_social_events(agent, world_state, previous_world_state)
            if social_events:
                current_mood = self._analyze_social_impact(agent, social_events, current_mood)
        
        return current_mood
    
    def _apply_mood_decay(self, mood: Dict[str, Any]) -> Dict[str, Any]:
        """Apply natural mood decay over time."""
        if mood['intensity'] > 0:
            mood['intensity'] = max(0, int(mood['intensity'] * self.decay_rate))
            
            # If intensity drops to 0, return to neutral
            if mood['intensity'] == 0:
                mood['type'] = 'neutral'
                mood['reason'] = 'Mood naturally subsided'
        
        return mood
    
    def _apply_physical_effects(self, agent: 'AIAgent', mood: Dict[str, Any]) -> Dict[str, Any]:
        """Apply rule-based physical effects on mood."""
        energy = agent.state.get('energy', 100)
        
        # Energy-based mood changes
        if energy <= self.energy_thresholds['exhausted']:
            if mood['type'] != 'exhausted' or mood['intensity'] < 40:
                return {
                    'type': 'exhausted',
                    'intensity': 40,
                    'reason': 'My energy is critically low'
                }
        elif energy <= self.energy_thresholds['tired']:
            if mood['type'] == 'neutral' or mood['intensity'] < 20:
                return {
                    'type': 'tired',
                    'intensity': 20,
                    'reason': 'I am feeling tired'
                }
        elif energy >= self.energy_thresholds['energetic']:
            if mood['type'] in ['exhausted', 'tired']:
                return {
                    'type': 'energetic',
                    'intensity': 30,
                    'reason': 'I feel refreshed and energetic'
                }
        
        # Boredom from inactivity (simplified rule)
        if mood['type'] == 'neutral' and mood['intensity'] == 0:
            # Small chance of developing boredom
            import random
            if random.random() < 0.1:  # 10% chance per tick
                return {
                    'type': 'bored',
                    'intensity': 15,
                    'reason': 'Nothing interesting is happening'
                }
        
        return mood
    
    def _detect_social_events(self, agent: 'AIAgent', current_state: Dict[str, Any], 
                            previous_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect social events that might affect the agent's mood."""
        events = []
        
        # Find agent in both states
        current_agent = self._find_agent_in_state(agent.id, current_state)
        previous_agent = self._find_agent_in_state(agent.id, previous_state)
        
        if not current_agent or not previous_agent:
            return events
        
        # Detect speech directed at this agent
        for other_agent in current_state.get('agents', []):
            if other_agent['id'] == agent.id:
                continue
                
            # Check if someone said something and is nearby
            if other_agent.get('last_utterance'):
                other_pos = other_agent.get('position', {})
                agent_pos = current_agent.get('position', {})
                
                # Calculate distance
                distance = abs(other_pos.get('x', 0) - agent_pos.get('x', 0)) + abs(other_pos.get('y', 0) - agent_pos.get('y', 0))
                
                if distance <= 2:  # Within hearing range
                    events.append({
                        'type': 'speech_received',
                        'source_agent': other_agent['id'],
                        'source_role': other_agent.get('role', 'unknown'),
                        'content': other_agent['last_utterance'],
                        'distance': distance
                    })
        
        return events
    
    def _find_agent_in_state(self, agent_id: str, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find an agent in the world state."""
        for agent in state.get('agents', []):
            if agent.get('id') == agent_id:
                return agent
        return None
    
    def _analyze_social_impact(self, agent: 'AIAgent', events: List[Dict[str, Any]], 
                             current_mood: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to analyze the emotional impact of social events."""
        if not events:
            return current_mood
        
        # Prepare event descriptions for LLM analysis
        event_descriptions = []
        for event in events:
            if event['type'] == 'speech_received':
                desc = f"{event['source_role']} {event['source_agent']} said to you: '{event['content']}'"
                event_descriptions.append(desc)
        
        if not event_descriptions:
            return current_mood
        
        # Call LLM for emotional analysis
        try:
            analysis_result = self._call_emotion_analysis_llm(agent, event_descriptions)
            if analysis_result:
                return self._apply_llm_mood_change(current_mood, analysis_result)
        except Exception as e:
            print(f"Emotion analysis failed for {agent.id}: {e}")
        
        return current_mood
    
    def _call_emotion_analysis_llm(self, agent: 'AIAgent', event_descriptions: List[str]) -> Optional[Dict[str, Any]]:
        """Call LLM for emotion analysis."""
        events_text = "\\n".join([f"- {desc}" for desc in event_descriptions])
        
        prompt = f"""### Emotion Analysis Task ###
You are an emotion analyzer. An AI agent with the following personality was involved in events. Analyze the events and determine the emotional impact.

Agent Personality: {agent.personality}
Agent Role: {agent.role}
Current Mood: {agent.state.get('mood', {}).get('type', 'neutral')} (intensity: {agent.state.get('mood', {}).get('intensity', 0)})

Events that happened:
{events_text}

Respond ONLY with a JSON object with three keys:
- "mood_change" (string): New emotion type if changed, or "no_change"
- "intensity_delta" (integer): Change in intensity (-100 to +100)
- "reason" (string): Brief explanation of the emotional impact

Example: {{"mood_change": "angry", "intensity_delta": 25, "reason": "Insulted by guard"}}"""
        
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/project-chimera",
            "X-Title": "Project Chimera Emotion Analysis"
        }
        
        payload = {
            "model": Config.DEFAULT_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # Lower temperature for more consistent analysis
            "max_tokens": 200
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15  # Shorter timeout for emotion analysis
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    
                    # Try to parse JSON response
                    try:
                        return json.loads(content.strip())
                    except json.JSONDecodeError:
                        # Try to extract JSON from text
                        import re
                        json_match = re.search(r'\\{[^{}]*\\}', content)
                        if json_match:
                            return json.loads(json_match.group())
            
        except Exception as e:
            print(f"Emotion analysis API call failed: {e}")
        
        return None
    
    def _apply_llm_mood_change(self, current_mood: Dict[str, Any], 
                              analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Apply LLM analysis results to current mood."""
        mood_change = analysis.get('mood_change', 'no_change')
        intensity_delta = analysis.get('intensity_delta', 0)
        reason = analysis.get('reason', 'Social interaction')
        
        if mood_change == 'no_change':
            # Just adjust intensity
            new_intensity = max(0, min(100, current_mood['intensity'] + intensity_delta))
            return {
                'type': current_mood['type'],
                'intensity': new_intensity,
                'reason': current_mood['reason'] if intensity_delta == 0 else reason
            }
        else:
            # Change mood type
            new_intensity = max(0, min(100, abs(intensity_delta)))
            return {
                'type': mood_change,
                'intensity': new_intensity,
                'reason': reason
            }
    
    def get_mood_description(self, mood: Dict[str, Any]) -> str:
        """Get a human-readable description of the mood."""
        mood_type = mood.get('type', 'neutral')
        intensity = mood.get('intensity', 0)
        
        if intensity == 0:
            return 'neutral'
        elif intensity < 30:
            return f'slightly {mood_type}'
        elif intensity < 60:
            return f'moderately {mood_type}'
        else:
            return f'very {mood_type}'
    
    def should_affect_behavior(self, mood: Dict[str, Any]) -> bool:
        """Determine if the current mood should significantly affect behavior."""
        return mood.get('intensity', 0) > 30