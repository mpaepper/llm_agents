import os
from openai import OpenAI, AsyncOpenAI
from pydantic import BaseModel, field_serializer
from typing import List, Any


class ChatLLM(BaseModel):
    model: str = 'gpt-3.5-turbo'
    temperature: float = 0.0
    api_key: str = None
    client: Any = None
    async_client: Any = None
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
    @field_serializer('client')
    def serialize_client(self, client: Any, _info):
        # Don't serialize the client
        return None
        
    @field_serializer('async_client')
    def serialize_async_client(self, async_client: Any, _info):
        # Don't serialize the async client
        return None

    def __init__(self, **data):
        super().__init__(**data)
        # Use provided API key or get from environment
        if self.api_key is None:
            self.api_key = os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Provide it as a parameter or set OPENAI_API_KEY environment variable.")
        
        # Initialize OpenAI clients
        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)

    def generate(self, prompt: str, stop: List[str] = None):
        """Synchronous version of generate"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            stop=stop
        )
        return response.choices[0].message.content
        
    async def generate_async(self, prompt: str, stop: List[str] = None):
        """Asynchronous version of generate"""
        response = await self.async_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            stop=stop
        )
        return response.choices[0].message.content

if __name__ == '__main__':
    llm = ChatLLM()
    result = llm.generate(prompt='Who is the president of the USA?')
    print(result)
    
    # Example of async usage
    import asyncio
    
    async def test_async():
        llm = ChatLLM()
        result = await llm.generate_async(prompt='Who is the president of the USA?')
        print(result)
        
    # asyncio.run(test_async())
