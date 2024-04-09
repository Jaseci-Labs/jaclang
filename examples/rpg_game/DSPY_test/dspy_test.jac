import:py sys;
import:py os;
import:py dspy;

"""Classify emotion among sadness, joy, love, anger, fear, surprise."""
obj Emotion:dspy.Signature:{

    static has sentence:Any = dspy.InputField(desc = "Sentence");
    static has sentiment:Any = dspy.OutputField(desc = "Sentiment");
}

with entry{
    gpt3_turbo:Any = dspy.OpenAI(model='gpt-3.5-turbo-1106', max_tokens=300);
    dspy.configure(lm=gpt3_turbo);

    sentence:str = "i started feeling a little vulnerable when the giant spotlight started blinding me";  # from dair-ai/emotion

    classify = dspy.Predict(Emotion);
    print(classify(sentence=sentence).sentiment);
}