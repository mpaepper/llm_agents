import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..config import Settings
from llm_agents import Agent, ChatLLM, PythonREPLTool, HackerNewsSearchTool, SerpAPITool

logger = logging.getLogger(__name__)

class AgentManager:
    """Service for managing LLM agents."""
    
    def __init__(self, settings: Settings):
        """Initialize the agent manager."""
        self.settings = settings
        self.agents: Dict[str, Dict] = {}
        self.tasks: Dict[str, Dict] = {}
        self.results: Dict[str, Dict] = {}
        
        # Initialize available tools
        self.available_tools = {
            "python_repl": PythonREPLTool,
            "hacker_news": HackerNewsSearchTool,
        }
        
        # Add SerpAPI tool if API key is provided
        if settings.serpapi_api_key:
            self.available_tools["google_search"] = SerpAPITool
        
        logger.info(f"Agent manager initialized with {len(self.available_tools)} available tools")
    
    def list_agents(self) -> List[Dict]:
        """List all available agents."""
        return list(self.agents.values())
    
    def create_agent(self, agent_data: Dict) -> Dict:
        """Create a new agent."""
        agent_id = str(uuid.uuid4())
        model = agent_data.get("model") or self.settings.default_model
        
        # Validate model
        if model not in self.settings.available_models:
            logger.warning(f"Invalid model {model}, using default {self.settings.default_model}")
            model = self.settings.default_model
        
        # Create agent record
        agent = {
            "id": agent_id,
            "name": agent_data["name"],
            "description": agent_data["description"],
            "model": model,
            "tools": agent_data.get("tools", []),
            "status": "ready",
            "created_at": datetime.now().isoformat(),
        }
        
        self.agents[agent_id] = agent
        logger.info(f"Created agent {agent_id}: {agent['name']}")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent details."""
        return self.agents.get(agent_id)
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Deleted agent {agent_id}")
            return True
        return False
    
    def create_task(self, agent_id: str, task_data: Dict) -> Dict:
        """Create a new task for an agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "agent_id": agent_id,
            "prompt": task_data["prompt"],
            "parameters": task_data.get("parameters", {}),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        
        self.tasks[task_id] = task
        logger.info(f"Created task {task_id} for agent {agent_id}")
        
        # Run the task asynchronously in a real implementation
        # For now, we'll just mark it as completed
        self.tasks[task_id]["status"] = "completed"
        
        return task
    
    def list_tasks(self) -> List[Dict]:
        """List all tasks."""
        return list(self.tasks.values())
    
    def get_task_result(self, task_id: str) -> Optional[Dict]:
        """Get task result."""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        result = self.results.get(task_id, {})
        
        return {
            "task": task,
            "result": result,
        }
    
    def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all available tools for agents."""
        return [
            {"id": tool_id, "name": tool_class.__name__, "description": tool_class.__doc__}
            for tool_id, tool_class in self.available_tools.items()
        ]
    
    def run_agent_query(
        self, 
        agent_id: str, 
        query: str, 
        max_iterations: int = 10,
        tools: Optional[List[str]] = None
    ) -> Dict:
        """Run a query through an agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent_config = self.agents[agent_id]
        
        # Initialize tools
        agent_tools = []
        tool_ids = tools or agent_config["tools"]
        
        for tool_id in tool_ids:
            if tool_id in self.available_tools:
                # Initialize the tool with appropriate API keys
                if tool_id == "google_search" and self.settings.serpapi_api_key:
                    agent_tools.append(self.available_tools[tool_id](api_key=self.settings.serpapi_api_key.get_secret_value()))
                else:
                    agent_tools.append(self.available_tools[tool_id]())
        
        # Initialize LLM
        llm = ChatLLM(model=agent_config["model"], api_key=self.settings.openai_api_key.get_secret_value())
        
        # Initialize agent
        agent = Agent(llm=llm, tools=agent_tools)
        
        # Run the query
        start_time = time.time()
        logger.info(f"Running query for agent {agent_id}: {query}")
        
        try:
            result = agent.run(query, max_iterations=max_iterations)
            execution_time = time.time() - start_time
            
            # Store the result
            response = {
                "result": result,
                "thinking": agent.thinking,
                "iterations": len(agent.thinking),
                "execution_time": execution_time,
            }
            
            logger.info(f"Query completed for agent {agent_id} in {execution_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error running query: {str(e)}")
            raise 