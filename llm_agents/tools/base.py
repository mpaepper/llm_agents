from pydantic import BaseModel
from contextvars import ContextVar
from functools import wraps
from uuid import uuid4


# Context-local so shared tools cannot mix independent or concurrent Agent runs.
tool_run_id = ContextVar('tool_run_id', default=None)


def tool_run(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        token = tool_run_id.set(str(uuid4()))
        try:
            return func(*args, **kwargs)
        finally:
            tool_run_id.reset(token)
    return wrapped

class ToolInterface(BaseModel):
    name: str
    description: str
    
    def use(self, input_text: str) -> str:
        raise NotImplementedError("use() method not implemented")  # Implement in subclass
