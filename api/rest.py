"""
REST API endpoints for Project Prometheus
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from api.websockets import manager

router = APIRouter()

class ExperimentConfig(BaseModel):
    """Configuration for starting an experiment"""
    duration_days: int = 14
    agent_count: int = 6
    
class InterventionRequest(BaseModel):
    """Request to intervene on an agent"""
    agent_id: str
    changes: Dict[str, Any]

@router.get("/")
async def api_root():
    """API root endpoint"""
    return {"message": "Project Prometheus API v1.0"}

@router.post("/experiment/start")
async def start_experiment(config: ExperimentConfig = ExperimentConfig()):
    """Start a new experiment"""
    try:
        await manager.start_experiment()
        return {"message": "Experiment started successfully", "config": config.dict()}
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