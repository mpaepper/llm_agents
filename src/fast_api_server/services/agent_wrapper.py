import logging
import re
from typing import List, Dict, Any
from src.llm_agents import Agent

logger = logging.getLogger(__name__)

# Constants from the Agent class
FINAL_ANSWER_TOKEN = "Final Answer:"
OBSERVATION_TOKEN = "Observation:"
THOUGHT_TOKEN = "Thought:"
ACTION_TOKEN = "Action:"
ACTION_INPUT_TOKEN = "Action Input:"

class AgentWrapper:
    """Wrapper for the Agent class to add thinking functionality."""
    
    def __init__(self, agent: Agent):
        """Initialize the agent wrapper."""
        self.agent = agent
        self.thinking = []
        self.current_step = None
        
        # Store original run method
        self._original_run = agent.run
        
        # Monkey patch the run method
        def wrapped_run(question, max_iterations=None):
            # Reset thinking for new run
            self.thinking = []
            self.current_step = None
            
            # Set max_loops if that attribute exists and max_iterations is provided
            if hasattr(self.agent, 'max_loops') and max_iterations is not None:
                original_max_loops = self.agent.max_loops
                self.agent.max_loops = max_iterations
                
                # Call original run method
                result = self._original_run(question)
                
                # Restore original max_loops
                self.agent.max_loops = original_max_loops
            else:
                # Call original run method
                result = self._original_run(question)
            
            # If the agent already has thinking, use that
            if hasattr(self.agent, 'thinking') and self.agent.thinking:
                self.thinking = self.agent.thinking
            
            # If we don't have any thinking steps yet, create a final step with the result
            if not self.thinking:
                self.thinking.append({
                    "step": 1,
                    "thought": "Thinking process not captured",
                    "action": "Final Answer",
                    "action_input": "Not available",
                    "result": result
                })
            
            return result
        
        # Replace the run method
        self.agent.run = wrapped_run
    
    def run(self, question, max_iterations=None):
        """Run the agent with the given question."""
        return self.agent.run(question, max_iterations=max_iterations)
    
    def _extract_content(self, text, token):
        """Extract content after a token until the next token."""
        pattern = f"{token}(.*?)(?:{THOUGHT_TOKEN}|{ACTION_TOKEN}|{ACTION_INPUT_TOKEN}|{OBSERVATION_TOKEN}|{FINAL_ANSWER_TOKEN}|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return "" 