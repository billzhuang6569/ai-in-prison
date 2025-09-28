"""
Data Logging Pipeline for Project Chimera

This module provides structured logging capabilities for capturing
simulation events, agent decisions, and world state changes.
"""

import json
import os
import queue
import threading
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
        
        # Initialize queue and worker thread for non-blocking I/O
        self.log_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._write_loop, daemon=True)
        self.worker_thread.start()
        
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
            "file_type": "decision",
            **decision_data
        }
        
        # Put log entry into queue for non-blocking processing
        self.log_queue.put(log_entry)
    
    def _write_loop(self) -> None:
        """
        Background thread loop for processing log entries from the queue.
        This method runs continuously until a sentinel value (None) is received.
        """
        while True:
            try:
                # Block until a log entry is available
                log_entry = self.log_queue.get()
                
                # Check for sentinel value to exit
                if log_entry is None:
                    break
                
                # Process the log entry based on its type
                file_type = log_entry.get('file_type', 'event')
                
                if file_type == 'decision':
                    # Write to decisions file
                    self._write_jsonl(self.decisions_file, log_entry)
                    # Display on console
                    self._render_decision_console(
                        log_entry.get('agent_id'),
                        log_entry.get('tick'),
                        {k: v for k, v in log_entry.items() if k not in ['timestamp', 'session_id', 'agent_id', 'tick', 'type', 'file_type']}
                    )
                elif file_type == 'world_state':
                    # Write to world state file
                    self._write_jsonl(self.world_state_file, log_entry)
                    # Display summary on console
                    self._render_world_state_console(log_entry.get('state', {}))
                elif file_type == 'event':
                    # Write to events file
                    self._write_jsonl(self.events_file, log_entry)
                    # Display on console based on event type
                    event_type = log_entry.get('type', 'info')
                    event_data = {k: v for k, v in log_entry.items() if k not in ['timestamp', 'session_id', 'type', 'file_type']}
                    
                    if event_type == "error":
                        self.console.print(f"[bold red]ERROR:[/bold red] {event_data}")
                    elif event_type == "warning":
                        self.console.print(f"[bold yellow]WARNING:[/bold yellow] {event_data}")
                    elif event_type in ["info", "session_start"]:
                        self.console.print(f"[blue]INFO:[/blue] {event_data}")
                
                # Mark task as done
                self.log_queue.task_done()
                
            except Exception as e:
                # Handle any errors in the background thread
                self.console.print(f"[bold red]Logger thread error: {e}[/bold red]")
                # Continue processing other entries
                continue
    
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
            "file_type": "world_state",
            "tick": world_state.get('tick', 0),
            "state": world_state
        }
        
        # Put log entry into queue for non-blocking processing
        self.log_queue.put(log_entry)
    
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
            "file_type": "event",
            **event_data
        }
        
        # Put log entry into queue for non-blocking processing
        self.log_queue.put(log_entry)
    
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
    
    def close(self) -> None:
        """
        Gracefully close the logger by stopping the background thread
        and ensuring all queued log entries are processed.
        """
        # Send sentinel value to stop the worker thread
        self.log_queue.put(None)
        
        # Wait for the worker thread to finish processing all entries
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)  # Wait up to 5 seconds
            
        # Log session end
        self.console.print(f"[bold green]Simulation Logger closed for session: {self.session_id}[/bold green]")