```jac
expert=getExpert(question)
```

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed. 

[Information]
None

[Inputs and Input Type Information]
question (str) question='What are Large Language Models?'

[Output Type]
str

[Output Type Explanations]
expert name (str)

[Action]
get the best person to answer the question

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```
Result
```yml
[Output] An expert in the field of Natural Language Processing or Artificial Intelligence.
```
---
```jac
answer=getAnswerForQuestion(question,expert)
```

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed. 

[Information]
None

[Inputs and Input Type Information]
question (str) question='What are Large Language Models?'
expert (str) expert =An expert in the field of Natural Language Processing or Artificial Intelligence

[Output Type]
str

[Output Type Explanations]
answer for the question (str)

[Action]
get the answer for the question from the expert(professional)

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```
Result
```yml
[Output] Large Language Models are advanced artificial intelligence models that have been trained on massive amounts of text data to understand and generate human-like text.
```