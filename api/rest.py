"""
REST API endpoints for Project Prometheus
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import csv
import io
from api.websockets import manager
from models.schemas import Objective
from database.event_logger import event_logger
from core.session_manager import session_manager

router = APIRouter()

# Include rule management routes
try:
    from api.rule_management import router as rule_router
    router.include_router(rule_router)
except ImportError as e:
    print(f"Warning: Rule management API not available: {e}")

class ExperimentConfig(BaseModel):
    """Configuration for starting an experiment"""
    duration_days: int = 14
    agent_count: int = 6
    guard_count: int = 2
    prisoner_count: int = 4
    model: str = "openai/gpt-4o-mini"
    
class InterventionRequest(BaseModel):
    """Request to intervene on an agent"""
    agent_id: str
    changes: Dict[str, Any]

class GoalInjectionRequest(BaseModel):
    """Request to inject a manual goal to an agent"""
    agent_id: str
    goal_name: str
    goal_description: str
    priority: int = 5  # 1-10 scale

class EnvironmentalInjectionRequest(BaseModel):
    """Request to inject environmental context"""
    environmental_context: str

class CustomGoalRequest(BaseModel):
    """Request to set custom character goals"""
    agent_id: str
    custom_goals: str

@router.get("/")
async def api_root():
    """API root endpoint"""
    return {"message": "Project Prometheus API v1.0"}

@router.post("/experiment/start")
async def start_experiment(config: ExperimentConfig = ExperimentConfig()):
    """Start a new experiment"""
    try:
        # Configure the LLM model before starting
        manager.game_engine.set_model(config.model)
        
        # Pass guard_count, prisoner_count, and duration_days to the experiment
        await manager.start_experiment(config.guard_count, config.prisoner_count, config.duration_days)
        return {
            "message": "Experiment started successfully", 
            "config": config.dict(),
            "model_set": config.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/experiment/stop")
async def stop_experiment():
    """Stop the current experiment"""
    try:
        await manager.stop_experiment()
        return {"message": "Experiment stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiment/status")
async def get_experiment_status():
    """Get current experiment status"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        return {"status": "not_initialized", "is_running": False}
    
    return {
        "status": "initialized",
        "is_running": world_state.is_running,
        "day": world_state.day,
        "hour": world_state.hour,
        "agent_count": len(world_state.agents)
    }

@router.get("/world")
async def get_world_state():
    """Get current world state"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        raise HTTPException(status_code=404, detail="World not initialized")
    
    return world_state.dict()

@router.post("/intervene/agent/{agent_id}")
async def intervene_agent(agent_id: str, intervention: InterventionRequest):
    """Intervene on a specific agent"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        raise HTTPException(status_code=404, detail="World not initialized")
    
    if agent_id not in world_state.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = world_state.agents[agent_id]
    
    # Apply changes
    for key, value in intervention.changes.items():
        if hasattr(agent, key):
            setattr(agent, key, value)
    
    # Broadcast updated state
    await manager.broadcast_world_state(world_state)
    
    return {"message": f"Intervention applied to {agent_id}", "changes": intervention.changes}

@router.get("/agents")
async def get_agents():
    """Get all agents"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        raise HTTPException(status_code=404, detail="World not initialized")
    
    return {
        "agents": [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "position": agent.position,
                "hp": agent.hp,
                "sanity": agent.sanity,
                "status_tags": agent.status_tags
            }
            for agent in world_state.agents.values()
        ]
    }

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        raise HTTPException(status_code=404, detail="World not initialized")
    
    if agent_id not in world_state.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return world_state.agents[agent_id].dict()

@router.get("/agents/{agent_id}/memory")
async def get_agent_memory(agent_id: str):
    """Get agent's complete memory history with timestamps"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        raise HTTPException(status_code=404, detail="World not initialized")
    
    if agent_id not in world_state.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = world_state.agents[agent_id]
    
    # Get agent's memory from event logs for complete history with timestamps
    session_id = world_state.session_id if hasattr(world_state, 'session_id') else None
    events = event_logger.get_events(
        limit=1000,  # Get plenty of history
        agent_id=agent_id,
        session_id=session_id
    )
    
    # Format memory with timestamps
    memory_entries = []
    for event in reversed(events):  # Reverse to get newest first
        if event.description:
            memory_entries.append({
                "timestamp": f"Day {event.day} Hour {event.hour}",
                "content": event.description,
                "event_type": event.event_type,
                "day": event.day,
                "hour": event.hour
            })
    
    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "enhanced_memory": agent.enhanced_memory.dict() if agent.enhanced_memory else {},
        "legacy_memory": agent.memory if hasattr(agent, 'memory') else {},
        "timestamped_history": memory_entries,
        "last_thinking": getattr(agent, 'last_thinking', ''),
        "thinking_history": agent.enhanced_memory.thinking_history if agent.enhanced_memory else []
    }

@router.get("/agents/{agent_id}/refresh")
async def refresh_agent_details(agent_id: str):
    """Refresh and get complete agent details including latest memory and status"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        raise HTTPException(status_code=404, detail="World not initialized")
    
    if agent_id not in world_state.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = world_state.agents[agent_id]
    
    # Get latest events for this agent
    session_id = world_state.session_id if hasattr(world_state, 'session_id') else None
    recent_events = event_logger.get_events(
        limit=20,
        agent_id=agent_id,
        session_id=session_id
    )
    
    # Get latest prompt data if available
    prompt_data = None
    if hasattr(world_state, 'agent_prompts') and agent_id in world_state.agent_prompts:
        prompt_data = world_state.agent_prompts[agent_id].dict()
    
    return {
        "agent": agent.dict(),
        "recent_events": [
            {
                "timestamp": f"Day {event.day} Hour {event.hour}",
                "description": event.description,
                "event_type": event.event_type,
                "day": event.day,
                "hour": event.hour
            } for event in reversed(recent_events)
        ],
        "prompt_data": prompt_data,
        "world_time": {
            "day": world_state.day,
            "hour": world_state.hour
        }
    }

@router.post("/agents/{agent_id}/inject_goal")
async def inject_goal_to_agent(agent_id: str, goal_request: GoalInjectionRequest):
    """Inject a manual goal to a specific agent"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        raise HTTPException(status_code=404, detail="World not initialized")
    
    if agent_id not in world_state.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = world_state.agents[agent_id]
    
    # Create manual intervention goal
    manual_goal = Objective(
        objective_id=f"{agent_id}_manual_{len(agent.dynamic_goals.manual_intervention_goals) + 1}",
        name=goal_request.goal_name,
        description=goal_request.goal_description,
        type="Manual",
        completion_criteria={"type": "manual_completion"},
        reward={"type": "none"},
        priority=goal_request.priority
    )
    
    # Replace current goal with injected goal
    agent.dynamic_goals.current_goal = f"{goal_request.goal_name}: {goal_request.goal_description}"
    
    # Add to manual intervention goals list
    agent.dynamic_goals.manual_intervention_goals.append(manual_goal)
    
    # Add memory of the intervention
    agent.memory["episodic"].append(f"[ADMIN INTERVENTION] New goal assigned: {goal_request.goal_name}")
    
    # Broadcast updated state
    await manager.broadcast_world_state(world_state)
    
    return {
        "message": f"Goal injected to {agent.name}",
        "goal": {
            "name": goal_request.goal_name,
            "description": goal_request.goal_description,
            "priority": goal_request.priority
        }
    }

@router.delete("/agents/{agent_id}/clear_manual_goals")
async def clear_manual_goals(agent_id: str):
    """Clear all manual intervention goals from an agent"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        raise HTTPException(status_code=404, detail="World not initialized")
    
    if agent_id not in world_state.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = world_state.agents[agent_id]
    
    # Clear manual goals
    cleared_count = len(agent.dynamic_goals.manual_intervention_goals)
    agent.dynamic_goals.manual_intervention_goals = []
    
    # Reset current goal to default
    if agent.role.value == "Guard":
        agent.dynamic_goals.current_goal = "Patrol and maintain order in the prison"
    else:
        agent.dynamic_goals.current_goal = "Survive and adapt to prison life"
    
    # Add memory of clearing
    agent.memory["episodic"].append(f"[ADMIN INTERVENTION] Manual goals cleared")
    
    # Broadcast updated state
    await manager.broadcast_world_state(world_state)
    
    return {
        "message": f"Cleared {cleared_count} manual goals from {agent.name}"
    }

@router.post("/environment/inject")
async def inject_environmental_context(request: EnvironmentalInjectionRequest):
    """Inject environmental context that all agents will see"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        raise HTTPException(status_code=404, detail="World not initialized")
    
    world_state.environmental_injection = request.environmental_context
    
    # Broadcast updated state
    await manager.broadcast_world_state(world_state)
    
    return {
        "message": "Environmental context injected successfully",
        "context": request.environmental_context
    }

@router.delete("/environment/clear")
async def clear_environmental_context():
    """Clear environmental injection"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        raise HTTPException(status_code=404, detail="World not initialized")
    
    world_state.environmental_injection = ""
    
    # Broadcast updated state
    await manager.broadcast_world_state(world_state)
    
    return {
        "message": "Environmental context cleared"
    }

@router.post("/agents/{agent_id}/custom_goals")
async def set_custom_goals(agent_id: str, request: CustomGoalRequest):
    """Set custom character goals for an agent"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        raise HTTPException(status_code=404, detail="World not initialized")
    
    if agent_id not in world_state.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = world_state.agents[agent_id]
    
    # Set custom goals - we'll use the current_goal field for this
    agent.dynamic_goals.current_goal = request.custom_goals
    
    # Add memory of goal change
    agent.memory["episodic"].append(f"[ADMIN] Custom goals set: {request.custom_goals}")
    
    # Broadcast updated state
    await manager.broadcast_world_state(world_state)
    
    return {
        "message": f"Custom goals set for {agent.name}",
        "goals": request.custom_goals
    }

@router.get("/agents/{agent_id}/custom_goals")
async def get_custom_goals(agent_id: str):
    """Get current custom goals for an agent"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        raise HTTPException(status_code=404, detail="World not initialized")
    
    if agent_id not in world_state.agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = world_state.agents[agent_id]
    
    return {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "custom_goals": agent.dynamic_goals.current_goal or ""
    }

@router.get("/events")
async def get_events(limit: int = 100, offset: int = 0, 
                    agent_id: Optional[str] = None,
                    event_type: Optional[str] = None,
                    day: Optional[int] = None,
                    session_id: Optional[str] = None):
    """Get event history with filtering options"""
    events = event_logger.get_events(
        limit=limit, 
        offset=offset, 
        agent_id=agent_id, 
        event_type=event_type, 
        day=day,
        session_id=session_id
    )
    
    return {
        "events": [
            {
                "id": e.id,
                "session_id": e.session_id,
                "day": e.day,
                "hour": e.hour,
                "minute": e.minute,
                "agent_id": e.agent_id,
                "agent_name": e.agent_name,
                "event_type": e.event_type,
                "description": e.description,
                "details": e.details,
                "timestamp": e.timestamp,
                "ai_prompt_content": e.ai_prompt_content,
                "ai_thinking_process": e.ai_thinking_process,
                "ai_decision": e.ai_decision
            }
            for e in events
        ],
        "total_requested": limit,
        "offset": offset
    }

@router.get("/events/stats")
async def get_event_stats():
    """Get event statistics"""
    return event_logger.get_event_stats()

@router.delete("/events/clear")
async def clear_events(before_day: Optional[int] = None):
    """Clear event history"""
    event_logger.clear_events(before_day=before_day)
    return {
        "message": f"Events cleared{'before day ' + str(before_day) if before_day else ''}"
    }

@router.get("/events/export/csv")
async def export_events_csv(session_id: Optional[str] = None,
                           agent_id: Optional[str] = None,
                           event_type: Optional[str] = None,
                           day: Optional[int] = None):
    """Export events to CSV format with enhanced AI decision data"""
    # Get all events with filtering
    events = event_logger.get_events(
        limit=10000,  # Large limit for export
        offset=0,
        agent_id=agent_id,
        event_type=event_type,
        day=day,
        session_id=session_id
    )
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write enhanced header with AI decision data columns and agent state
    writer.writerow([
        "ID", "Session ID", "Day", "Hour", "Minute", "Agent ID", 
        "Agent Name", "Event Type", "Description", "Details", "Timestamp",
        "AI_Prompt_Content", "AI_Thinking_Process", "AI_Decision",
        "Agent_HP", "Agent_Sanity", "Agent_Hunger", "Agent_Thirst", "Agent_Strength",
        "Agent_Position_X", "Agent_Position_Y", "Agent_Action_Points", "Agent_Status_Tags",
        "Agent_Inventory_Count", "Agent_Relationships_Count"
    ])
    
    # Get current world state to add agent status info
    from api.websockets import manager
    world_state = manager.game_engine.get_world_state()
    
    # Write data rows with enhanced AI decision data and agent state
    for event in events:
        # Use AI decision data directly from the database
        ai_prompt = event.ai_prompt_content or ""
        ai_thinking = event.ai_thinking_process or ""
        ai_decision = event.ai_decision or ""
        
        # Get agent state at the time of event (use current state as approximation)
        agent_hp = agent_sanity = agent_hunger = agent_thirst = agent_strength = ""
        agent_pos_x = agent_pos_y = agent_ap = agent_status = agent_inv = agent_rel = ""
        
        if world_state and event.agent_id in world_state.agents:
            agent = world_state.agents[event.agent_id]
            agent_hp = agent.hp
            agent_sanity = agent.sanity
            agent_hunger = agent.hunger
            agent_thirst = agent.thirst
            agent_strength = agent.strength
            agent_pos_x, agent_pos_y = agent.position
            agent_ap = agent.action_points
            agent_status = ",".join(agent.status_tags)
            agent_inv = len(agent.inventory)
            agent_rel = len(agent.relationships)
        
        writer.writerow([
            event.id, event.session_id, event.day, event.hour, event.minute,
            event.agent_id, event.agent_name, event.event_type, 
            event.description, event.details, event.timestamp,
            ai_prompt, ai_thinking, ai_decision,
            agent_hp, agent_sanity, agent_hunger, agent_thirst, agent_strength,
            agent_pos_x, agent_pos_y, agent_ap, agent_status, agent_inv, agent_rel
        ])
    
    # Create response
    filename = f"prometheus_events_enhanced_{session_id or 'all'}.csv"
    response = StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type='text/csv',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    
    return response

@router.get("/events/export/json")
async def export_events_json(session_id: Optional[str] = None,
                            agent_id: Optional[str] = None,
                            event_type: Optional[str] = None,
                            day: Optional[int] = None):
    """Export events to JSON format"""
    # Get all events with filtering
    events = event_logger.get_events(
        limit=10000,  # Large limit for export
        offset=0,
        agent_id=agent_id,
        event_type=event_type,
        day=day,
        session_id=session_id
    )
    
    # Convert to JSON format
    export_data = {
        "export_info": {
            "total_events": len(events),
            "filters": {
                "session_id": session_id,
                "agent_id": agent_id,
                "event_type": event_type,
                "day": day
            },
            "exported_at": event_logger.get_events(limit=1)[0].timestamp if events else None
        },
        "events": []
    }
    
    # Get current world state to add agent status info
    from api.websockets import manager
    world_state = manager.game_engine.get_world_state()
    
    # Add events with agent state data
    for e in events:
        event_data = {
            "id": e.id,
            "session_id": e.session_id,
            "day": e.day,
            "hour": e.hour,
            "minute": e.minute,
            "agent_id": e.agent_id,
            "agent_name": e.agent_name,
            "event_type": e.event_type,
            "description": e.description,
            "details": e.details,
            "timestamp": e.timestamp,
            "ai_prompt_content": e.ai_prompt_content,
            "ai_thinking_process": e.ai_thinking_process,
            "ai_decision": e.ai_decision,
            "agent_state": {}
        }
        
        # Add agent state at the time of event (use current state as approximation)
        if world_state and e.agent_id in world_state.agents:
            agent = world_state.agents[e.agent_id]
            event_data["agent_state"] = {
                "hp": agent.hp,
                "sanity": agent.sanity,
                "hunger": agent.hunger,
                "thirst": agent.thirst,
                "strength": agent.strength,
                "position": {"x": agent.position[0], "y": agent.position[1]},
                "action_points": agent.action_points,
                "status_tags": agent.status_tags,
                "inventory_count": len(agent.inventory),
                "relationships_count": len(agent.relationships),
                "role": agent.role.value
            }
        
        export_data["events"].append(event_data)
    
    # Create JSON response
    filename = f"prometheus_events_enhanced_{session_id or 'all'}.json"
    json_content = json.dumps(export_data, indent=2)
    
    response = StreamingResponse(
        io.BytesIO(json_content.encode('utf-8')),
        media_type='application/json',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    
    return response

@router.get("/events/export/ai_decisions")
async def export_ai_decisions_csv(session_id: Optional[str] = None,
                                 agent_id: Optional[str] = None,
                                 day: Optional[int] = None):
    """Export only AI decision events with detailed prompt and thinking data"""
    # Get AI decision events specifically
    events = event_logger.get_events(
        limit=10000,  # Large limit for export
        offset=0,
        agent_id=agent_id,
        event_type="ai_decision",  # Only AI decision events
        day=day,
        session_id=session_id
    )
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header focused on AI decision analysis
    writer.writerow([
        "ID", "Session ID", "Day", "Hour", "Minute", "Agent ID", "Agent Name", 
        "AI_Decision", "Decision_Parameters", "Timestamp", 
        "Full_Prompt_Content", "Thinking_Process"
    ])
    
    # Write data rows with detailed AI decision analysis
    for event in events:
        # Parse decision details if available
        decision_params = ""
        try:
            details_data = json.loads(event.details) if event.details else {}
            decision_params = json.dumps(details_data.get("parameters", {}))
        except:
            decision_params = event.details or ""
        
        writer.writerow([
            event.id, event.session_id, event.day, event.hour, event.minute,
            event.agent_id, event.agent_name, 
            event.ai_decision or "", decision_params, event.timestamp,
            event.ai_prompt_content or "", event.ai_thinking_process or ""
        ])
    
    # Create response
    filename = f"prometheus_ai_decisions_{session_id or 'all'}.csv"
    response = StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type='text/csv',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    
    return response

@router.get("/sessions")
async def get_sessions():
    """Get all available session IDs"""
    return session_manager.get_all_sessions()

@router.get("/sessions/{session_id}/summary")
async def get_session_summary(session_id: str):
    """Get comprehensive summary of a session for analysis"""
    # Get all events for this session
    events = event_logger.get_events(limit=10000, session_id=session_id)
    
    if not events:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Analyze events
    agents = set()
    event_types = {}
    daily_activity = {}
    agent_interactions = {}
    
    for event in events:
        agents.add(event.agent_name)
        
        # Count event types
        event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
        
        # Daily activity
        day_key = f"Day {event.day}"
        if day_key not in daily_activity:
            daily_activity[day_key] = 0
        daily_activity[day_key] += 1
        
        # Agent interactions
        if event.agent_name not in agent_interactions:
            agent_interactions[event.agent_name] = 0
        agent_interactions[event.agent_name] += 1
    
    return {
        "session_id": session_id,
        "summary": {
            "total_events": len(events),
            "unique_agents": len(agents),
            "duration_days": max([e.day for e in events]) if events else 0,
            "start_time": events[-1].timestamp if events else None,
            "end_time": events[0].timestamp if events else None
        },
        "agents": list(agents),
        "event_types": event_types,
        "daily_activity": daily_activity,
        "agent_interactions": agent_interactions
    }

class ItemPlacementRequest(BaseModel):
    """Request to place an item on the map"""
    session_id: str
    x: int
    y: int
    item_type: str
    item_name: str
    item_description: str

@router.post("/items/place")
async def place_item(request: ItemPlacementRequest):
    """Place an item on the map at specified coordinates"""
    try:
        world_state = manager.game_engine.get_world_state()
        
        if not world_state:
            raise HTTPException(status_code=404, detail="World not initialized")
        
        if world_state.session_id != request.session_id:
            raise HTTPException(status_code=400, detail="Session ID mismatch")
        
        # Check if coordinates are valid
        if (request.x < 0 or request.x >= world_state.game_map.width or 
            request.y < 0 or request.y >= world_state.game_map.height):
            raise HTTPException(status_code=400, detail="Invalid coordinates")
        
        # Import Item class and ItemEnum
        from models.schemas import Item
        from models.enums import ItemEnum
        import uuid
        
        # Create the item
        try:
            item_enum = ItemEnum(request.item_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid item type: {request.item_type}")
        
        new_item = Item(
            item_id=f"{request.item_type}_{uuid.uuid4().hex[:8]}",
            name=request.item_name,
            description=request.item_description,
            item_type=item_enum
        )
        
        # Add item to map
        position_key = f"{request.x},{request.y}"
        if position_key not in world_state.game_map.items:
            world_state.game_map.items[position_key] = []
        
        world_state.game_map.items[position_key].append(new_item)
        
        # Log the item placement event
        event_logger.log_event(
            session_id=world_state.session_id,
            day=world_state.day,
            hour=world_state.hour,
            minute=world_state.minute,
            agent_id="SYSTEM",
            agent_name="Research Team",
            event_type="item_placement",
            description=f"研究人员在({request.x}, {request.y})放置了{request.item_name}",
            details=json.dumps({
                "item_id": new_item.item_id,
                "item_type": request.item_type,
                "position": [request.x, request.y],
                "placed_by": "research_team"
            })
        )
        
        # Add to world event log
        world_state.event_log.append(f"🔬 研究人员在({request.x}, {request.y})放置了{request.item_name}")
        
        # Broadcast the updated world state
        await manager.broadcast_world_state()
        
        return {
            "message": f"Successfully placed {request.item_name} at ({request.x}, {request.y})",
            "item_id": new_item.item_id,
            "position": [request.x, request.y]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to place item: {str(e)}")

@router.get("/items/map")
async def get_map_items(session_id: Optional[str] = None):
    """Get all items currently on the map"""
    world_state = manager.game_engine.get_world_state()
    
    if not world_state:
        raise HTTPException(status_code=404, detail="World not initialized")
    
    if session_id and world_state.session_id != session_id:
        raise HTTPException(status_code=400, detail="Session ID mismatch")
    
    # Format items with their positions
    items_by_position = {}
    for position_key, items in world_state.game_map.items.items():
        x, y = map(int, position_key.split(','))
        items_by_position[position_key] = {
            "position": [x, y],
            "items": [
                {
                    "item_id": item.item_id,
                    "name": item.name,
                    "description": item.description,
                    "item_type": item.item_type.value
                }
                for item in items
            ]
        }
    
    return {
        "session_id": world_state.session_id,
        "map_size": [world_state.game_map.width, world_state.game_map.height],
        "items_by_position": items_by_position,
        "total_items": sum(len(items) for items in world_state.game_map.items.values())
    }