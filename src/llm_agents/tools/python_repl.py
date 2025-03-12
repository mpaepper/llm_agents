import sys
import re
import asyncio
from io import StringIO
from typing import Dict, Optional

from pydantic import BaseModel, Field
from llm_agents.tools.base import ToolInterface


# Taken from https://github.com/hwchase17/langchain/blob/master/langchain/python.py
class PythonREPL(BaseModel):
    """Simulates a standalone Python REPL."""

    globals: Optional[Dict] = Field(default_factory=dict, alias="_globals")
    locals: Optional[Dict] = Field(default_factory=dict, alias="_locals")

    def run(self, command: str) -> str:
        """Run command with own globals/locals and returns anything printed."""
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        try:
            exec(command, self.globals, self.locals)
            sys.stdout = old_stdout
            output = mystdout.getvalue()
        except Exception as e:
            sys.stdout = old_stdout
            output = str(e)
        return output
        
    async def run_async(self, command: str) -> str:
        """Async version of run - uses an executor to avoid blocking the event loop."""
        return await asyncio.to_thread(self.run, command)


def _get_default_python_repl() -> PythonREPL:
    return PythonREPL(_globals=globals(), _locals=None)


class PythonREPLTool(ToolInterface):
    """A tool for running python code in a REPL."""

    name: str = "Python REPL"
    description: str = (
        "A Python shell. Use this to execute python commands. "
        "Input should be a valid python command. "
        "If you want to see the output of a value, you should print it out "
        "with `print(...)`."
    )
    python_repl: PythonREPL = Field(default_factory=_get_default_python_repl)

    def use(self, input_text: str) -> str:
        """Synchronous version of use"""
        # Strip any leading/trailing whitespace
        input_text = input_text.strip()
        
        # Remove code block formatting with regex
        # This handles cases like ```python, ```py, etc.
        if input_text.startswith("```"):
            # Match the opening code fence with optional language identifier
            pattern = r"^```[\w]*\s*(.*?)```\s*$"
            match = re.search(pattern, input_text, re.DOTALL)
            if match:
                input_text = match.group(1).strip()
            else:
                # Fallback to simple stripping if regex doesn't match
                input_text = input_text.strip("```").strip()
        
        return self.python_repl.run(input_text)
        
    async def use_async(self, input_text: str) -> str:
        """Asynchronous version of use"""
        # Strip any leading/trailing whitespace
        input_text = input_text.strip()
        
        # Remove code block formatting with regex
        # This handles cases like ```python, ```py, etc.
        if input_text.startswith("```"):
            # Match the opening code fence with optional language identifier
            pattern = r"^```[\w]*\s*(.*?)```\s*$"
            match = re.search(pattern, input_text, re.DOTALL)
            if match:
                input_text = match.group(1).strip()
            else:
                # Fallback to simple stripping if regex doesn't match
                input_text = input_text.strip("```").strip()
        
        return await self.python_repl.run_async(input_text)


if __name__ == '__main__':
    repl_tool = PythonREPLTool()
    result = repl_tool.use('print(5 * 7)')
    assert result == "35\n"
    print(result)
    
    # Test with code block
    code_block = '''```python
    print(5 * 7)
    ```'''
    result = repl_tool.use(code_block)
    assert result == "35\n"
    print(result)
    
    # Example of async usage
    import asyncio
    
    async def test_async():
        repl_tool = PythonREPLTool()
        result = await repl_tool.use_async('print(5 * 7)')
        assert result == "35\n"
        print(result)
        
    # asyncio.run(test_async())
