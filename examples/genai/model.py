from jaclang.core.model import ModelClass
from openai import OpenAI
import anthropic
import os


class OpenAIModel(ModelClass):
    def __init__(self, model_name: str = "gpt-4", api_key: str = None) -> None:
        self.model_name = model_name
        self.api_key = api_key if api_key else os.getenv("OPENAI_API_KEY")
        self.model = OpenAI(api_key=self.api_key)

    def __infer__(
        self,
        input: str,
        model: str = None,
        temperature: float = 0.5,
        max_tokens: int = 1024,
    ) -> None:
        model = model if model else self.model_name
        x = self.model.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": input}],
        ).choices[0]
        return x.message.content

class ClaudeModel(ModelClass):
    def __init__(self, model_name: str = "claude-3-sonnet-20240229", api_key: str = None) -> None:
        self.model_name = model_name
        self.api_key = api_key if api_key else os.getenv("ANTHROPIC_API_KEY")
        self.model = anthropic.Anthropic(api_key=self.api_key)

    def __infer__(
        self,
        input: str,
        model: str = None,
        temperature: float = 0.5,
        max_tokens: int = 1024,
    ) -> None:
        model = model if model else self.model_name
        x = self.model.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": input}],
        )
        return x.content[0].text