import:py sys;
import:py os;
import:py dspy;

# """Answer the given question"""
# obj GenerateSearchQuery:dspy.Signature: {

#     can postinit{
#         self.question:dspy.InputField = dspy.InputField(desc = "Q");
#         self.result:dspy.OutputField = dspy.OutputField(desc = "Out");
#     }
# }

"""Classify emotion among sadness, joy, love, anger, fear, surprise."""
obj Emotion:dspy.Signature:{

    can postinit{
        self.sentence:dspy.InputField = dspy.InputField(desc = "Sentence");
        self.sentiment:dspy.OutputField = dspy.OutputField(desc = "Sentiment");
    }
    # has sentence:Any = dspy.InputField(desc = "Sentence");
    # has sentiment:Any = dspy.OutputField(desc = "Sentiment");
}

with entry{
    gpt3_turbo:Any = dspy.OpenAI(model='gpt-3.5-turbo-1106', max_tokens=300);
    dspy.configure(lm=gpt3_turbo);

    # print(gpt3_turbo("Who is Albert Einstein"));

    # gen_ai = dspy.ChainOfThought(GenerateSearchQuery);
    # print(gen_ai(question="Who is Albert Einstein").result);

    sentence:str = "i started feeling a little vulnerable when the giant spotlight started blinding me";  # from dair-ai/emotion

    classify = dspy.Predict(Emotion);
    classify(sentence=sentence);
}