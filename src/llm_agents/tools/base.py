from pydantic import BaseModel

class ToolInterface(BaseModel):
    name: str
    description: str
    
    def use(self, input_text: str) -> str:
        """Synchronous version of the tool use method"""
        raise NotImplementedError("use() method not implemented")  # Implement in subclass
        
    async def use_async(self, input_text: str) -> str:
        """Asynchronous version of the tool use method
        
        By default, this calls the synchronous version. Override this method
        in subclasses that need true async behavior.
        """
        return self.use(input_text)  # Default implementation calls sync version
