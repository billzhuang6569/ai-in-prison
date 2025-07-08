"""
Event logging system with SQLite database for complete event history
"""

import sqlite3
import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import threading
import os

@dataclass
class EventRecord:
    id: Optional[int]
    session_id: str
    day: int
    hour: int
    minute: int
    agent_id: str
    agent_name: str
    event_type: str  # "action", "speech", "system", "combat", etc.
    description: str
    details: str  # JSON string for additional details
    timestamp: str

class EventLogger:
    """Thread-safe event logger with SQLite backend"""
    
    def __init__(self, db_path: str = "database/events.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the database and create tables if needed"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            
            # First, create the table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day INTEGER NOT NULL,
                    hour INTEGER NOT NULL,
                    minute INTEGER NOT NULL,
                    agent_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    details TEXT,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Check if session_id column exists and add it if not
            cursor = conn.execute("PRAGMA table_info(events)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'session_id' not in columns:
                print("Adding session_id column to existing events table...")
                conn.execute("ALTER TABLE events ADD COLUMN session_id TEXT NOT NULL DEFAULT 'legacy_session'")
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON events(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON events(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_day_hour ON events(day, hour)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)")
            
            conn.commit()
            conn.close()
    
    def log_event(self, session_id: str, day: int, hour: int, minute: int, agent_id: str, 
                  agent_name: str, event_type: str, description: str, 
                  details: str = "") -> int:
        """Log a new event and return the event ID"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                INSERT INTO events (session_id, day, hour, minute, agent_id, agent_name, 
                                  event_type, description, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, day, hour, minute, agent_id, agent_name, event_type, 
                  description, details, timestamp))
            
            event_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return event_id
    
    def get_events(self, limit: int = 100, offset: int = 0, 
                   agent_id: Optional[str] = None, 
                   event_type: Optional[str] = None,
                   day: Optional[int] = None,
                   session_id: Optional[str] = None) -> List[EventRecord]:
        """Get events with optional filtering"""
        
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
            
        if day is not None:
            query += " AND day = ?"
            params.append(day)
            
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        query += " ORDER BY day DESC, hour DESC, minute DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            events = []
            for row in cursor.fetchall():
                events.append(EventRecord(
                    id=row["id"],
                    session_id=row["session_id"],
                    day=row["day"],
                    hour=row["hour"], 
                    minute=row["minute"],
                    agent_id=row["agent_id"],
                    agent_name=row["agent_name"],
                    event_type=row["event_type"],
                    description=row["description"],
                    details=row["details"],
                    timestamp=row["timestamp"]
                ))
            
            conn.close()
            return events
    
    def get_recent_events_for_agent(self, agent_id: str, session_id: str, limit: int = 10) -> List[str]:
        """Get recent event descriptions for an agent (for memory system)"""
        events = self.get_events(limit=limit, agent_id=agent_id, session_id=session_id)
        return [f"Day {e.day}h{e.hour}m{e.minute}: {e.description}" for e in events]
    
    def clear_events(self, before_day: Optional[int] = None):
        """Clear events, optionally only before a certain day"""
        query = "DELETE FROM events"
        params = []
        
        if before_day is not None:
            query += " WHERE day < ?"
            params.append(before_day)
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(query, params)
            conn.commit()
            conn.close()
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Get statistics about logged events"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            
            # Total events
            total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            
            # Events by type
            type_stats = {}
            for row in conn.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type"):
                type_stats[row[0]] = row[1]
            
            # Events by agent
            agent_stats = {}
            for row in conn.execute("SELECT agent_name, COUNT(*) FROM events GROUP BY agent_name"):
                agent_stats[row[0]] = row[1]
                
            conn.close()
            
            return {
                "total_events": total,
                "events_by_type": type_stats,
                "events_by_agent": agent_stats
            }

# Global event logger instance
event_logger = EventLogger()