```jac
question = "What are Large Language Models?";
expert = get_expert(question);
```

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are needed. 

[Information]
None

[Inputs and Input Type Information]
Question (str) (question) = 'What are Large Language Models?'

[Output Type]
str

[Output Type Explanations]
Expert  Profession (str)

[Action]
Finds the best professional to answer the given question

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```
Result
```yml
[Output] Artificial Intelligence Researcher
```
---
```jac
answer = get_answer(question, expert);
```

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed. 

[Information]
None

[Inputs and Input Type Information]
Question (str) (question) = 'What are Large Language Models?'
Expert (str) (expert) = 'Artificial Intelligence Researcher'

[Output Type]
str

[Output Type Explanations]
Expert's Answer (str)

[Action]
Get the answer for the question from expert's perspective

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```
Result
```yml
[Output] Large Language Models are advanced artificial intelligence models that have been trained on a large amount of text data
```