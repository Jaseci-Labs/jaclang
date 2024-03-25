import:py os;
import:py from jaclang.core.model, ModelClass;

class OpenAI:ModelClass: {
    can init(model_name: str = "GPT-3", api_key: str = None) {
        self.model_name = model_name;
        self.api_key =  api_key if api_key else os.getenv("OPENAI_API_KEY");
    }
    can __infer__(input: str, temperature: float, max_tokens: int) {
        return f"OpenAI model {self.model_name} infers: {input} using {temperature} as temp and {max_tokens} tokens.";
    }
}

model llm: OpenAI{
    model_name = "GPT-4";
}

with entry {
    print(llm.__infer__("Hello World", temperature=0.5, max_tokens=10));
}