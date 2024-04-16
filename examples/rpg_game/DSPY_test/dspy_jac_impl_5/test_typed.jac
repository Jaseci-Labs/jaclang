import:py from pydantic, BaseModel, Field;
import:py sys;
import:py os;
import:py dspy;

obj Input:BaseModel:{
    static has context: str = Field(description="The context for the question");
    static has query: str = Field(description="The question to be answered");
}

obj Output:BaseModel:{
    static has answer: str = Field(description="The answer for the question");
    static has confidence: float = Field(ge=0, le=1, description="The confidence score for the answer");
}

"""Answer the question based on the context and query provided, and on the scale of 10 tell how confident you are about the answer."""
obj QASignature:dspy.Signature:{
    static has input: Input = dspy.InputField();
    static has output: Output = dspy.OutputField();
}

with entry {
    gpt3_turbo:Any = dspy.OpenAI(model='gpt-3.5-turbo-1106', max_tokens=300);
    dspy.configure(lm=gpt3_turbo);

    predictor = dspy.TypedPredictor(QASignature);
    print(predictor(input=Input(context="The capital of France is Paris.", query="What is the capital of France?")));

}