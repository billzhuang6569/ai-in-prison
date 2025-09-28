"""
Data Logging Pipeline for Project Chimera

This module provides structured logging capabilities for capturing
simulation events, agent decisions, and world state changes.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from config import Config


class SimulationLogger:
    """
    Structured logger for simulation events with file output and console display.
    
    Captures:
    - Agent decision processes
    - World state changes
    - System events and errors
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize the simulation logger.
        
        Args:
            session_id: Unique identifier for this simulation session
        """
        self.session_id = session_id or Config.SESSION_ID
        self.log_dir = Path(Config.LOG_DIR)
        
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize log files
        self.decisions_file = self.log_dir / f"{self.session_id}_decisions.jsonl"
        self.world_state_file = self.log_dir / f"{self.session_id}_world_state.jsonl"
        self.events_file = self.log_dir / f"{self.session_id}_events.jsonl"
        
        # Initialize rich console for pretty output
        self.console = Console()
        
        # Log session start
        self._log_event("session_start", {"session_id": self.session_id})
        self.console.print(f"[bold green]Simulation Logger initialized for session: {self.session_id}[/bold green]")
    
    def log_decision(self, agent_id: str, tick: int, decision_data: Dict[str, Any]) -> None:
        """
        Log an agent's decision process.
        
        Args:
            agent_id: ID of the agent making the decision
            tick: Current simulation tick
            decision_data: Dictionary containing decision details
        """
        timestamp = datetime.now().isoformat()
        
        # Prepare log entry
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "agent_id": agent_id,
            "tick": tick,
            "type": "decision",
            **decision_data
        }
        
        # Write to decisions file
        self._write_jsonl(self.decisions_file, log_entry)
        
        # Display on console
        self._render_decision_console(agent_id, tick, decision_data)
    
    def log_world_state(self, world_state: Dict[str, Any]) -> None:
        """
        Log the current world state.
        
        Args:
            world_state: Complete world state dictionary
        """
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "type": "world_state",
            "tick": world_state.get('tick', 0),
            "state": world_state
        }
        
        # Write to world state file
        self._write_jsonl(self.world_state_file, log_entry)
        
        # Display summary on console
        self._render_world_state_console(world_state)
    
    def log_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Log a general simulation event.
        
        Args:
            event_type: Type of event (e.g., "error", "warning", "info")
            event_data: Event details
        """
        self._log_event(event_type, event_data)
    
    def _log_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Internal method to log events.
        
        Args:
            event_type: Type of event
            event_data: Event details
        """
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "type": event_type,
            **event_data
        }
        
        # Write to events file
        self._write_jsonl(self.events_file, log_entry)
        
        # Display on console based on event type
        if event_type == "error":
            self.console.print(f"[bold red]ERROR:[/bold red] {event_data}")
        elif event_type == "warning":
            self.console.print(f"[bold yellow]WARNING:[/bold yellow] {event_data}")
        elif event_type in ["info", "session_start"]:
            self.console.print(f"[blue]INFO:[/blue] {event_data}")
    
    def _write_jsonl(self, file_path: Path, data: Dict[str, Any]) -> None:
        """
        Write data to a JSONL file.
        
        Args:
            file_path: Path to the JSONL file
            data: Data to write
        """
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        except Exception as e:
            self.console.print(f"[bold red]Failed to write to {file_path}: {e}[/bold red]")
    
    def _render_decision_console(self, agent_id: str, tick: int, decision_data: Dict[str, Any]) -> None:
        """
        Render agent decision on console with rich formatting.
        
        Args:
            agent_id: Agent ID
            tick: Current tick
            decision_data: Decision details
        """
        # Extract key information
        thought = decision_data.get('parsed_action', {}).get('_thought', 'No thought recorded')
        action = decision_data.get('parsed_action', {})
        error = decision_data.get('error')
        
        # Create action description
        action_type = action.get('type', 'unknown')
        action_desc = self._format_action_description(action)
        
        # Create panel content
        content = Text()
        content.append(f"Tick {tick}\n", style="bold cyan")
        content.append(f"Thought: ", style="bold")
        content.append(f"{thought}\n", style="italic")
        content.append(f"Action: ", style="bold")
        content.append(f"{action_desc}", style="green" if not error else "red")
        
        if error:
            content.append(f"\nError: {error}", style="bold red")
        
        # Display panel
        panel = Panel(
            content,
            title=f"[bold]{agent_id}[/bold]",
            border_style="blue" if not error else "red",
            width=80
        )
        
        self.console.print(panel)
    
    def _render_world_state_console(self, world_state: Dict[str, Any]) -> None:
        """
        Render world state summary on console.
        
        Args:
            world_state: World state dictionary
        """
        tick = world_state.get('tick', 0)
        agents = world_state.get('agents', [])
        
        # Create summary table
        table = Table(title=f"World State - Tick {tick}")
        table.add_column("Agent ID", style="cyan")
        table.add_column("Role", style="magenta")
        table.add_column("Position", style="green")
        table.add_column("Last Action", style="yellow")
        
        for agent in agents:
            agent_id = agent.get('id', 'unknown')
            role = agent.get('role', 'unknown')
            pos = agent.get('position', {})
            position = f"({pos.get('x', '?')}, {pos.get('y', '?')})"
            last_utterance = agent.get('last_utterance', 'None')
            
            table.add_row(agent_id, role, position, last_utterance)
        
        self.console.print(table)
        self.console.print()  # Add spacing
    
    def _format_action_description(self, action: Dict[str, Any]) -> str:
        """
        Format action dictionary into readable description.
        
        Args:
            action: Action dictionary
            
        Returns:
            Formatted action description
        """
        action_type = action.get('type', 'unknown')
        
        if action_type == 'move':
            target = action.get('target', {})
            return f"Move to ({target.get('x', '?')}, {target.get('y', '?')})"
        elif action_type == 'wait':
            return "Wait"
        elif action_type == 'say':
            content = action.get('content', '')
            return f"Say: '{content}'"
        else:
            return f"Unknown action: {action_type}"
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current logging session.
        
        Returns:
            Dictionary with session statistics
        """
        stats = {
            "session_id": self.session_id,
            "log_directory": str(self.log_dir),
            "files": {}
        }
        
        # Check file sizes and line counts
        for file_name, file_path in [
            ("decisions", self.decisions_file),
            ("world_state", self.world_state_file),
            ("events", self.events_file)
        ]:
            if file_path.exists():
                stats["files"][file_name] = {
                    "size_bytes": file_path.stat().st_size,
                    "line_count": sum(1 for _ in open(file_path, 'r'))
                }
            else:
                stats["files"][file_name] = {"size_bytes": 0, "line_count": 0}
        
        return stats