from pydantic import BaseModel
from llama_cpp import Llama
from typing import Type


class LlamaCppLLM(BaseModel):
    model: Type[Llama] = None
    seed: int = 1337,
    max_tokens: int = 256
    n_threads: int = 4,  # Number of threads to use.
    n_batch: int = 8,  # Maximum number of tokens to batch.
    n_ctx: int = 512,  # Token context window.
    top_k: int = 40,  # The top-k value to use for sampling.
    top_p: float = 0.95,  # The top-p value to use for sampling.
    temp: float = 0.8,  # The temperature to use for sampling.
    repeat_penalty: float = 1.1  # The penalty to apply to repeated tokens.,

    def __init__(self, model_path: str, **kwargs):
        super().__init__(**kwargs)
        self.model = Llama(model_path=model_path)

    def generate(self, prompt: str):
        response = self.model(prompt=prompt, max_tokens=self.max_tokens)
        return response['choices'][0]['text']


if __name__ == '__main__':
    llm = LlamaCppLLM(model_path='./models/llama-7B-ggml-model-q4_0.bin')
    result = llm.generate(prompt='Who is the president of the USA?')
    print(result)
