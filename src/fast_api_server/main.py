import logging
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import get_settings, Settings
from .logging_config import setup_logging
from .services.agent_service import AgentService

# Setup logging
setup_logging()
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

# Create FastAPI app
app = FastAPI(
    title="LLM Agent Server",
    description="A simple API for interacting with LLM agents",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_agent_service(settings: Settings = Depends(get_settings)):
    """Get agent service."""
    return AgentService(settings)

@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the LLM Agent Server",
        "docs": "/docs",
    }

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/tools", response_model=List[Dict[str, Any]], tags=["tools"])
async def list_available_tools(
    service: AgentService = Depends(get_agent_service)
):
    """List all available tools for agents."""
    logger.info("Listing available tools")
    return service.list_available_tools()

@app.post("/query", response_model=AgentResponse, tags=["agent"])
async def query_agent(
    query: AgentQuery,
    service: AgentService = Depends(get_agent_service)
):
    """Query an agent with a prompt (asynchronous)."""
    logger.info(f"Querying agent asynchronously: {query.query}")
    
    try:
        # Use the async version of run_agent_query
        result = await service.run_agent_query_async(
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
        
@app.post("/query/sync", response_model=AgentResponse, tags=["agent"])
async def query_agent_sync(
    query: AgentQuery,
    service: AgentService = Depends(get_agent_service)
):
    """Query an agent with a prompt (synchronous)."""
    logger.info(f"Querying agent synchronously: {query.query}")
    
    try:
        # Use the synchronous version but run it in a thread pool to avoid blocking
        import asyncio
        result = await asyncio.to_thread(
            service.run_agent_query,
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