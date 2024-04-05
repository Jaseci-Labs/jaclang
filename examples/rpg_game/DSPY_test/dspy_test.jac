import:py sys;
import:py os;
import:py from dspy, OpenAI;

with entry{
    gpt3_turbo:Any = dspy.OpenAI(model='gpt-3.5-turbo-1106', max_tokens=300);
    dspy.configure(lm=gpt3_turbo);

    print(gpt3_turbo("hello! this is a raw prompt to GPT-3.5"));

}