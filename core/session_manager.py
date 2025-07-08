"""
Session management for experiments
"""

import uuid
import datetime
from typing import Dict, Any, List
from database.event_logger import event_logger

class SessionManager:
    """Manages experiment sessions"""
    
    def __init__(self):
        self.current_session_id = None
        self.session_start_time = None
        self.session_metadata = {}
    
    def start_new_session(self) -> str:
        """Start a new experiment session and return the session ID"""
        # Generate a unique session ID with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]  # Short UUID
        self.current_session_id = f"session_{timestamp}_{unique_id}"
        
        self.session_start_time = datetime.datetime.now()
        self.session_metadata = {
            "start_time": self.session_start_time.isoformat(),
            "session_id": self.current_session_id
        }
        
        print(f"Started new experiment session: {self.current_session_id}")
        return self.current_session_id
    
    def get_current_session_id(self) -> str:
        """Get the current session ID"""
        if not self.current_session_id:
            return self.start_new_session()
        return self.current_session_id
    
    def end_session(self):
        """End the current session"""
        if self.current_session_id:
            print(f"Ended experiment session: {self.current_session_id}")
            self.current_session_id = None
            self.session_start_time = None
            self.session_metadata = {}
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        if not self.current_session_id:
            return {}
            
        duration = None
        if self.session_start_time:
            duration = (datetime.datetime.now() - self.session_start_time).total_seconds()
            
        return {
            "session_id": self.current_session_id,
            "start_time": self.session_start_time.isoformat() if self.session_start_time else None,
            "duration_seconds": duration,
            **self.session_metadata
        }
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all available sessions from the database"""
        try:
            # Get all events to find unique session IDs
            events = event_logger.get_events(limit=10000)
            session_data = {}
            
            for event in events:
                session_id = event.session_id
                if session_id not in session_data:
                    session_data[session_id] = {
                        "session_id": session_id,
                        "start_time": event.timestamp,
                        "end_time": event.timestamp,
                        "event_count": 0,
                        "agents": set(),
                        "days": set()
                    }
                
                # Update session data
                session_data[session_id]["event_count"] += 1
                session_data[session_id]["agents"].add(event.agent_name)
                session_data[session_id]["days"].add(event.day)
                
                # Update time range
                if event.timestamp > session_data[session_id]["end_time"]:
                    session_data[session_id]["end_time"] = event.timestamp
                if event.timestamp < session_data[session_id]["start_time"]:
                    session_data[session_id]["start_time"] = event.timestamp
            
            # Convert to list and clean up
            sessions = []
            for session_id, data in session_data.items():
                sessions.append({
                    "session_id": session_id,
                    "start_time": data["start_time"],
                    "end_time": data["end_time"],
                    "event_count": data["event_count"],
                    "agent_count": len(data["agents"]),
                    "days_count": len(data["days"]),
                    "agents": list(data["agents"]),
                    "days": sorted(list(data["days"]))
                })
            
            # Sort by start time (most recent first)
            sessions.sort(key=lambda x: x["start_time"], reverse=True)
            return sessions
            
        except Exception as e:
            print(f"Error getting sessions: {e}")
            return []

# Global session manager instance
session_manager = SessionManager()