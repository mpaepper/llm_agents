import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..config import get_settings, Settings
from ..services.agent_manager import AgentManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Models for request/response
class AgentQuery(BaseModel):
    """Model for querying an agent."""
    query: str
    max_iterations: Optional[int] = 10
    tools: Optional[List[str]] = None

class AgentResponse(BaseModel):
    """Model for agent response."""
    result: str
    thinking: List[Dict[str, Any]]
    iterations: int
    execution_time: float

# Dependency
def get_agent_manager(settings: Settings = Depends(get_settings)):
    """Get agent manager service."""
    return AgentManager(settings)

@router.post("/{agent_id}/query", response_model=AgentResponse)
async def query_agent(
    agent_id: str,
    query: AgentQuery,
    manager: AgentManager = Depends(get_agent_manager)
):
    """Query an agent with a prompt."""
    logger.info(f"Querying agent {agent_id}: {query.query}")
    
    agent = manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        result = manager.run_agent_query(
            agent_id=agent_id,
            query=query.query,
            max_iterations=query.max_iterations,
            tools=query.tools
        )
        return result
    except Exception as e:
        logger.error(f"Error querying agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying agent: {str(e)}"
        )

@router.get("/available-tools", response_model=List[Dict[str, Any]])
async def list_available_tools(
    manager: AgentManager = Depends(get_agent_manager)
):
    """List all available tools for agents."""
    logger.info("Listing available tools")
    return manager.list_available_tools() 