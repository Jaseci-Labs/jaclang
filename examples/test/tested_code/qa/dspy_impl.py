import dspy
llm = dspy.OllamaLocal(base_url="http://52.23.242.52:11343", model="phi3")
dspy.configure(lm=llm)
question = input()
answer = dspy.ChainOfThought('question -> answer')
response = answer(question=question)

print(response.answer)
