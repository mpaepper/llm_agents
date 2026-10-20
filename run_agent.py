import os

from llm_agents import (Agent, ChatLLM, PythonREPLTool, HackerNewsSearchTool,
                        SerpAPITool, ParallelSearchTool, ParallelFetchTool)


def default_tools():
    search_tools = ([SerpAPITool()] if os.environ.get('SERPAPI_API_KEY') else
                    [ParallelSearchTool(), ParallelFetchTool()])
    return [PythonREPLTool(), *search_tools, HackerNewsSearchTool()]

if __name__ == '__main__':
    prompt = input("Enter a question / task for the agent: ")
    agent = Agent(llm=ChatLLM(), tools=default_tools())
    result = agent.run(prompt)

    print(f"Final answer is {result}")
