"""Anthropic API client for MTLLM."""

import re

PROMPT_TEMPLATE = """
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed.
Input/Type formatting: Explanation of the Input (variable_name) (type) = value

[Information]
{information}

[Context]
{context}

[Inputs Information]
{inputs_information}

[Output Information]
{output_information}

[Type Explanations]
{type_explanations}

[Action]
{action}

{prompting_method}
"""  # noqa E501

WITH_REASON_SUFFIX = """
Reason and return the output result(s) only, adhering to the provided Type in the following format

[Reasoning] <Reason>
[Output] <Result>
"""

WITHOUT_REASON_SUFFIX = """Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
"""  # noqa E501

CHAIN_OF_THOUGHT = """Initially Lets Think Step by Step and then Generate the Output result(s) only, adhering to the provided Type in the following format

[Chain of Thought] <Thoughts>
[Output] <result>
"""  # noqa E501


class Anthropic:
    """Anthropic API client for MTLLM."""

    MTLLM_PROMPT: str = PROMPT_TEMPLATE
    MTLLM__PROMPTING_METHODS = {
        "normal": WITHOUT_REASON_SUFFIX,
        "reason-first": WITH_REASON_SUFFIX,
        "chain-of-thought": CHAIN_OF_THOUGHT,
    }

    def __init__(self, verbose: bool = False, **kwargs: dict) -> None:
        """Initialize the Anthropic API client."""
        import anthropic  # type: ignore

        self.client = anthropic.Anthropic()
        self.verbose = verbose
        self.model_name = kwargs.get("model_name", "claude-3-sonnet-20240229")
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 1024)

    def __infer__(self, meaning_in: str, **kwargs: dict) -> str:
        """Infer a response from the input meaning."""
        if self.verbose:
            print(f"Meaning In:\n{meaning_in}")
        messages = [{"role": "user", "content": meaning_in}]
        output = self.client.messages.create(
            model=kwargs.get("model_name", self.model_name),
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            messages=messages,
        )
        return output.content[0].text

    def __call__(self, input_text: str, **kwargs: dict) -> str:
        """Infer a response from the input text."""
        return self.__infer__(input_text, **kwargs)

    def resolve_output(self, meaning_out: str, method:str) -> dict:
        """Resolve the output string to return the reasoning and output."""
        if self.verbose:
            print(f"Meaning Out:\n{meaning_out}")
        output_match = re.search(r"\[Output\](.*)", meaning_out)
        output = output_match.group(1).strip() if output_match else None

        if method == "chain-of-thought":
            method_results_match = re.search(r"\[Chain of Thought\](.*)\[Output\]", meaning_out)
        elif method == "reason-first":
            method_results_match = re.search(r"\[Reasoning\](.*)\[Output\]", meaning_out)
        else:
            method_results_match = None
        method_results = method_results_match.group(1).strip() if method_results_match else None
        
        return {"method_results": method_results, "output": output}
