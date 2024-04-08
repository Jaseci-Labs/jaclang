import sys
import os
import dspy

gpt3_turbo = dspy.OpenAI(model='gpt-3.5-turbo-1106', max_tokens=300)
dspy.configure(lm=gpt3_turbo)

class Emotion(dspy.Signature):
    """Classify emotion among sadness, joy, love, anger, fear, surprise."""
    sentence = dspy.InputField()
    sentiment = dspy.OutputField()

sentence = "i started feeling a little vulnerable when the giant spotlight started blinding me"  # from dair-ai/emotion

classify = dspy.Predict(Emotion)
classify(sentence=sentence)