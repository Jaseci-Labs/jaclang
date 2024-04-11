from pydantic import BaseModel, Field
import sys
import os
import dspy

gpt3_turbo = dspy.OpenAI(model='gpt-3.5-turbo-1106', max_tokens=300)
dspy.configure(lm=gpt3_turbo)

class Input(BaseModel):
    context: str = Field(description="The context for the question")
    query: str = Field(description="The question to be answered")

class Output(BaseModel):
    answer: str = Field(description="The answer for the question")
    confidence: float = Field(ge=0, le=1, description="The confidence score for the answer")

class QASignature(dspy.Signature):
    """Answer the question based on the context and query provided, and on the scale of 10 tell how confident you are about the answer."""

    input: Input = dspy.InputField()
    output: Output = dspy.OutputField()

predictor = dspy.TypedPredictor(QASignature)
print(predictor(input=Input(context="The capital of France is Paris.", query="What is the capital of France?")))