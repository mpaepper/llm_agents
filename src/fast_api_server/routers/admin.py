import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..config import get_settings, Settings
from ..services.agent_manager import AgentManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Models for request/response
class AgentCreate(BaseModel):
    """Model for creating a new agent."""
    name: str
    description: str
    model: Optional[str] = None
    tools: List[str] = []

class AgentResponse(BaseModel):
    """Model for agent response."""
    id: str
    name: str
    description: str
    model: str
    tools: List[str]
    status: str
    created_at: str

class AgentList(BaseModel):
    """Model for listing agents."""
    agents: List[AgentResponse]

class AgentTask(BaseModel):
    """Model for creating a task for an agent."""
    prompt: str
    parameters: Optional[Dict] = None

class AgentTaskResponse(BaseModel):
    """Model for agent task response."""
    task_id: str
    agent_id: str
    status: str
    created_at: str

# Dependency
def get_agent_manager(settings: Settings = Depends(get_settings)):
    """Get agent manager service."""
    return AgentManager(settings)

@router.get("/", response_model=Dict)
async def admin_root():
    """Admin dashboard root."""
    return {
        "message": "Agent Admin Dashboard",
        "endpoints": {
            "agents": "/admin/agents",
            "tasks": "/admin/tasks",
        }
    }

@router.get("/agents", response_model=AgentList)
async def list_agents(
    manager: AgentManager = Depends(get_agent_manager)
):
    """List all available agents."""
    logger.info("Listing all agents")
    return {"agents": manager.list_agents()}

@router.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent: AgentCreate,
    manager: AgentManager = Depends(get_agent_manager)
):
    """Create a new agent."""
    logger.info(f"Creating new agent: {agent.name}")
    return manager.create_agent(agent)

@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    manager: AgentManager = Depends(get_agent_manager)
):
    """Get agent details."""
    logger.info(f"Getting agent details: {agent_id}")
    agent = manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    manager: AgentManager = Depends(get_agent_manager)
):
    """Delete an agent."""
    logger.info(f"Deleting agent: {agent_id}")
    success = manager.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return None

@router.post("/agents/{agent_id}/tasks", response_model=AgentTaskResponse)
async def create_task(
    agent_id: str,
    task: AgentTask,
    manager: AgentManager = Depends(get_agent_manager)
):
    """Create a new task for an agent."""
    logger.info(f"Creating new task for agent {agent_id}")
    return manager.create_task(agent_id, task)

@router.get("/tasks", response_model=List[AgentTaskResponse])
async def list_tasks(
    manager: AgentManager = Depends(get_agent_manager)
):
    """List all tasks."""
    logger.info("Listing all tasks")
    return manager.list_tasks()

@router.get("/tasks/{task_id}", response_model=Dict)
async def get_task_result(
    task_id: str,
    manager: AgentManager = Depends(get_agent_manager)
):
    """Get task result."""
    logger.info(f"Getting task result: {task_id}")
    result = manager.get_task_result(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result 