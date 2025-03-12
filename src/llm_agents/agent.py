import datetime
import re

from pydantic import BaseModel
from typing import List, Dict, Tuple
from llm_agents.llm import ChatLLM
from llm_agents.tools.base import ToolInterface
from llm_agents.tools.python_repl import PythonREPLTool


FINAL_ANSWER_TOKEN = "Final Answer:"
OBSERVATION_TOKEN = "Observation:"
THOUGHT_TOKEN = "Thought:"
PROMPT_TEMPLATE = """Today is {today} and you can use tools to get new information. Answer the question as best as you can using the following tools: 

{tool_description}

Use the following format:

Question: the input question you must answer
Thought: comment on what you want to do next
Action: the action to take, exactly one element of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation repeats N times, use it until you are sure of the answer)
Thought: I now know the final answer
Final Answer: your final answer to the original input question

Begin!

Question: {question}
Thought: {previous_responses}
"""


class Agent(BaseModel):
    llm: ChatLLM
    tools: List[ToolInterface]
    prompt_template: str = PROMPT_TEMPLATE
    max_loops: int = 15
    # The stop pattern is used, so the LLM does not hallucinate until the end
    stop_pattern: List[str] = [f'\n{OBSERVATION_TOKEN}', f'\n\t{OBSERVATION_TOKEN}']
    thinking: List[Dict] = []

    @property
    def tool_description(self) -> str:
        return "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])

    @property
    def tool_names(self) -> str:
        return ",".join([tool.name for tool in self.tools])

    @property
    def tool_by_names(self) -> Dict[str, ToolInterface]:
        return {tool.name: tool for tool in self.tools}

    def run(self, question: str, max_iterations: int = None):
        """Synchronous version of run"""
        # Reset thinking for new run
        self.thinking = []
        previous_responses = []
        num_loops = 0
        # Use provided max_iterations if specified, otherwise use self.max_loops
        max_loops = max_iterations if max_iterations is not None else self.max_loops
        
        prompt = self.prompt_template.format(
                today = datetime.date.today(),
                tool_description=self.tool_description,
                tool_names=self.tool_names,
                question=question,
                previous_responses='{previous_responses}'
        )
        print(prompt.format(previous_responses=''))
        while num_loops < max_loops:
            num_loops += 1
            curr_prompt = prompt.format(previous_responses='\n'.join(previous_responses))
            generated, tool, tool_input = self.decide_next_action(curr_prompt)
            
            # Record thinking step
            thinking_step = {
                "step": num_loops,
                "thought": generated,
                "tool": tool,
                "tool_input": tool_input
            }
            
            if tool == 'Final Answer':
                thinking_step["result"] = tool_input
                self.thinking.append(thinking_step)
                return tool_input
                
            if tool not in self.tool_by_names:
                raise ValueError(f"Unknown tool: {tool}")
                
            tool_result = self.tool_by_names[tool].use(tool_input)
            generated += f"\n{OBSERVATION_TOKEN} {tool_result}\n{THOUGHT_TOKEN}"
            
            # Add observation to thinking step
            thinking_step["observation"] = tool_result
            self.thinking.append(thinking_step)
            
            print(generated)
            previous_responses.append(generated)
        
        # If we reach max loops without a final answer
        return "I couldn't find a definitive answer within the allowed number of steps."
        
    async def run_async(self, question: str, max_iterations: int = None):
        """Asynchronous version of run"""
        # Reset thinking for new run
        self.thinking = []
        previous_responses = []
        num_loops = 0
        # Use provided max_iterations if specified, otherwise use self.max_loops
        max_loops = max_iterations if max_iterations is not None else self.max_loops
        
        prompt = self.prompt_template.format(
                today = datetime.date.today(),
                tool_description=self.tool_description,
                tool_names=self.tool_names,
                question=question,
                previous_responses='{previous_responses}'
        )
        print(prompt.format(previous_responses=''))
        while num_loops < max_loops:
            num_loops += 1
            curr_prompt = prompt.format(previous_responses='\n'.join(previous_responses))
            generated, tool, tool_input = await self.decide_next_action_async(curr_prompt)
            
            # Record thinking step
            thinking_step = {
                "step": num_loops,
                "thought": generated,
                "tool": tool,
                "tool_input": tool_input
            }
            
            if tool == 'Final Answer':
                thinking_step["result"] = tool_input
                self.thinking.append(thinking_step)
                return tool_input
                
            if tool not in self.tool_by_names:
                raise ValueError(f"Unknown tool: {tool}")
                
            tool_result = await self.tool_by_names[tool].use_async(tool_input)
            generated += f"\n{OBSERVATION_TOKEN} {tool_result}\n{THOUGHT_TOKEN}"
            
            # Add observation to thinking step
            thinking_step["observation"] = tool_result
            self.thinking.append(thinking_step)
            
            print(generated)
            previous_responses.append(generated)
        
        # If we reach max loops without a final answer
        return "I couldn't find a definitive answer within the allowed number of steps."

    def decide_next_action(self, prompt: str) -> Tuple[str, str, str]:
        """Synchronous version of decide_next_action"""
        generated = self.llm.generate(prompt, stop=self.stop_pattern)
        tool, tool_input = self._parse(generated)
        return generated, tool, tool_input
        
    async def decide_next_action_async(self, prompt: str) -> Tuple[str, str, str]:
        """Asynchronous version of decide_next_action"""
        generated = await self.llm.generate_async(prompt, stop=self.stop_pattern)
        tool, tool_input = self._parse(generated)
        return generated, tool, tool_input

    def _parse(self, generated: str) -> Tuple[str, str]:
        if FINAL_ANSWER_TOKEN in generated:
            return "Final Answer", generated.split(FINAL_ANSWER_TOKEN)[-1].strip()
        regex = r"Action: [\[]?(.*?)[\]]?[\n]*Action Input:[\s]*(.*)"
        match = re.search(regex, generated, re.DOTALL)
        if not match:
            raise ValueError(f"Output of LLM is not parsable for next tool use: `{generated}`")
        tool = match.group(1).strip()
        tool_input = match.group(2)
        return tool, tool_input.strip(" ").strip('"')


if __name__ == '__main__':
    agent = Agent(llm=ChatLLM(), tools=[PythonREPLTool()])
    result = agent.run("What is 7 * 9 - 34 in Python?")

    print(f"Final answer is {result}")
    print(f"Agent thinking: {agent.thinking}")
    
    # Example of async usage
    import asyncio
    
    async def test_async():
        agent = Agent(llm=ChatLLM(), tools=[PythonREPLTool()])
        result = await agent.run_async("What is 7 * 9 - 34 in Python?")
        print(f"Final answer is {result}")
        print(f"Agent thinking: {agent.thinking}")
        
    # asyncio.run(test_async())
