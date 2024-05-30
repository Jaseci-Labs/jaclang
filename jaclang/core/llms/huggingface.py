"""Huggingface client for MTLLM."""

from .base import BaseLLM


REASON_SUFFIX = """
Reason and return the output results(s) only such that <Output> should be eval(<Output>) Compatible and reflects the
expected output type, Follow the format below to provide the reasoning for the output result(s).

[Reasoning] <Reasoning>
[Output] <Output>
"""

NORMAL_SUFFIX = """Return the output result(s) only such that <Output> should be eval(<Output>) Compatible and
reflects the expected output type, Follow the format below to provide the output result(s).

[Output] <Output>
"""  # noqa E501

CHAIN_OF_THOUGHT_SUFFIX = """
Generate and return the output result(s) only, adhering to the provided Type in the following format. Perform the operation in a chain of thoughts.(Think Step by Step)

[Chain of Thoughts] <Chain of Thoughts>
[Output] <Result>
"""  # noqa E501

REACT_SUFFIX = """
"""  # noqa E501


class Huggingface(BaseLLM):
    """Huggingface API client for Large Language Models (LLMs)."""

    MTLLM_METHOD_PROMPTS: dict[str, str] = {
        "Normal": NORMAL_SUFFIX,
        "Reason": REASON_SUFFIX,
        "Chain-of-Thoughts": CHAIN_OF_THOUGHT_SUFFIX,
        "ReAct": REACT_SUFFIX,
    }

    def __init__(
        self, verbose: bool = False, max_tries: int = 10, **kwargs: dict
    ) -> None:
        """Initialize the Huggingface API client."""
        import torch  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline  # type: ignore

        torch.random.manual_seed(0)
        model = AutoModelForCausalLM.from_pretrained(
            kwargs.get("model_name", "microsoft/Phi-3-mini-128k-instruct"),
            device_map=kwargs.get("device_map", "cuda"),
            torch_dtype="auto",
            trust_remote_code=True,
        )
        tokenizer = AutoTokenizer.from_pretrained(
            kwargs.get("model_name", "microsoft/Phi-3-mini-128k-instruct")
        )
        self.verbose = verbose
        self.max_tries = max_tries
        self.pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_new_tokens", 1024)

    def __infer__(self, meaning_in: str, **kwargs: dict) -> str:
        """Infer a response from the input meaning."""
        messages = [{"role": "user", "content": meaning_in}]
        output = self.pipe(
            messages,
            temperature=kwargs.get("temperature", self.temperature),
            max_length=kwargs.get("max_new_tokens", self.max_tokens),
            **kwargs,
        )
        return output[0]["generated_text"][-1]["content"]
