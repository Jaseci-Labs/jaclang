from pydantic import BaseModel, Field
from enum import Enum
import dspy

llm = dspy.GROQ(model='llama3-70b-8192', api_key = "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")
dspy.settings.configure(lm=llm)

class Language(Enum):
    Spanish = "Spanish"
    English = "English"
    French = "French"

class Input(BaseModel):
    target_language: Language = Field(description="The target language to be translated into")
    essay: str = Field(description="The essay to be translated")

class Output(BaseModel):
    translated_text: str = Field(description="The translated text")

class QASignature(dspy.Signature):
    input: Input = dspy.InputField()
    output: Output = dspy.OutputField()

predictor = dspy.TypedChainOfThought(QASignature)

doc_query_pair = Input(
    essay="The quick brown fox jumps over the lazy dog",
    target_language= Language.Spanish
)

prediction = predictor(input=doc_query_pair)
print(prediction.output)
