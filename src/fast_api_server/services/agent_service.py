import logging
import time
import os
import asyncio
from typing import Dict, List, Optional, Any

from ..config import Settings
from src.llm_agents import Agent, ChatLLM, PythonREPLTool, HackerNewsSearchTool, SerpAPITool
from .agent_wrapper import AgentWrapper

logger = logging.getLogger(__name__)

class AgentService:
    """Service for interacting with LLM agents."""
    
    def __init__(self, settings: Settings):
        """Initialize the agent service."""
        self.settings = settings
        
        # Set environment variables for tools that might need them directly
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key.get_secret_value()
        if settings.serpapi_api_key:
            os.environ["SERPAPI_API_KEY"] = settings.serpapi_api_key.get_secret_value()
        
        # Initialize available tools
        self.available_tools = {
            "python_repl": PythonREPLTool,
            "hacker_news": HackerNewsSearchTool,
        }
        
        # Add SerpAPI tool if API key is provided
        if settings.serpapi_api_key:
            self.available_tools["google_search"] = SerpAPITool
        
        logger.info(f"Agent service initialized with {len(self.available_tools)} available tools")
    
    def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all available tools for agents."""
        return [
            {"id": tool_id, "name": tool_class.__name__, "description": tool_class.__doc__}
            for tool_id, tool_class in self.available_tools.items()
        ]
    
    def run_agent_query(
        self, 
        query: str, 
        max_iterations: int = 10,
        tools: Optional[List[str]] = None
    ) -> Dict:
        """Run a query through an agent (synchronous version)."""
        # Initialize tools
        agent_tools = []
        tool_ids = tools or list(self.available_tools.keys())
        
        for tool_id in tool_ids:
            if tool_id in self.available_tools:
                # Initialize the tool
                if tool_id == "google_search" and self.settings.serpapi_api_key:
                    agent_tools.append(self.available_tools[tool_id](api_key=self.settings.serpapi_api_key.get_secret_value()))
                else:
                    agent_tools.append(self.available_tools[tool_id]())
        
        # Initialize LLM with API key
        llm = ChatLLM(
            model=self.settings.default_model,
            api_key=self.settings.openai_api_key.get_secret_value()
        )
        
        # Initialize agent
        agent = Agent(llm=llm, tools=agent_tools)
        
        # Set max_loops directly if the attribute exists
        if hasattr(agent, 'max_loops'):
            agent.max_loops = max_iterations
        
        # Run the query
        start_time = time.time()
        logger.info(f"Running query: {query}")
        
        try:
            # Run the agent
            result = agent.run(query)
            execution_time = time.time() - start_time
            
            # Prepare response with minimal thinking information
            response = {
                "result": result,
                "thinking": [{"step": 1, "result": result}],
                "iterations": 1,
                "execution_time": execution_time,
            }
            
            logger.info(f"Query completed in {execution_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error running query: {str(e)}")
            raise
            
    async def run_agent_query_async(
        self, 
        query: str, 
        max_iterations: int = 10,
        tools: Optional[List[str]] = None
    ) -> Dict:
        """Run a query through an agent (asynchronous version)."""
        # Initialize tools
        agent_tools = []
        tool_ids = tools or list(self.available_tools.keys())
        
        for tool_id in tool_ids:
            if tool_id in self.available_tools:
                # Initialize the tool
                if tool_id == "google_search" and self.settings.serpapi_api_key:
                    agent_tools.append(self.available_tools[tool_id](api_key=self.settings.serpapi_api_key.get_secret_value()))
                else:
                    agent_tools.append(self.available_tools[tool_id]())
        
        # Initialize LLM with API key
        llm = ChatLLM(
            model=self.settings.default_model,
            api_key=self.settings.openai_api_key.get_secret_value()
        )
        
        # Initialize agent
        agent = Agent(llm=llm, tools=agent_tools)
        
        # Set max_loops directly if the attribute exists
        if hasattr(agent, 'max_loops'):
            agent.max_loops = max_iterations
        
        # Run the query
        start_time = time.time()
        logger.info(f"Running query asynchronously: {query}")
        
        try:
            # Run the agent asynchronously
            result = await agent.run_async(query)
            execution_time = time.time() - start_time
            
            # Prepare response with thinking information
            response = {
                "result": result,
                "thinking": agent.thinking,
                "iterations": len(agent.thinking),
                "execution_time": execution_time,
            }
            
            logger.info(f"Async query completed in {execution_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error running async query: {str(e)}")
            raise 