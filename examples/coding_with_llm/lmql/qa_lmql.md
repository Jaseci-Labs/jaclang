Jac
```python
qa = QA();
qa.get_answer("Where is Apple Computers headquartered?");
```
1st Iteration
```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed. 

[Information]
QA example with Thoughts and Actions (list[dict]) qa_example = [{"Question": "What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?","Thoughts and Observations": [{"Thought": "I need to search Colorado orogeny, find the area that the eastern sector of the Colorado ...","Action": "Search 'Colorado orogeny'","Observation": "The Colorado orogeny was an episode of mountain building (an orogeny) ..."},{"Thought": "It does not mention the eastern sector. So I need to look up eastern sector.","Action": "Search 'eastern sector of the Colorado orogeny'","Observation": "The eastern sector of the Colorado orogeny extends into the High Plains."},{"Thought": "High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.","Action": "Finish '1,800 to 7,000 ft'"}]}]

[Inputs and Input Type Information]
Question (str) question = "Where is Apple Computers headquartered?"
Previous Thoughts, Actions, and Observations (list[dict]) = []

[Output Type]
dict

[Output Type Explanations]
Next Thought and Action (dict)

[Action]
Get next Thought and Action

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```

Result
```yml
[Output] {"Thought": "I need to search for the headquarters of Apple Computers.", "Action": "Search 'Apple Computers headquarters'"}
```

2nd Iteration

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed. 

[Information]
QA example with Thoughts and Actions (list[dict]) qa_example = [{"Question": "What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?","Thoughts and Observations": [{"Thought": "I need to search Colorado orogeny, find the area that the eastern sector of the Colorado ...","Action": "Search 'Colorado orogeny'","Observation": "The Colorado orogeny was an episode of mountain building (an orogeny) ..."},{"Thought": "It does not mention the eastern sector. So I need to look up eastern sector.","Action": "Search 'eastern sector of the Colorado orogeny'","Observation": "The eastern sector of the Colorado orogeny extends into the High Plains."},{"Thought": "High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.","Action": "Finish '1,800 to 7,000 ft'"}]}]

[Inputs and Input Type Information]
Question (str) question = "Where is Apple Computers headquartered?"
Previous Thoughts, Actions, and Observations (list[dict]) = [{"Thought": "I need to search for the headquarters of Apple Computers.", "Action": "Search 'Apple Computers headquarters'", "Observation": "Apple Inc. (formerly Apple Computer, Inc.) is an American multinational technology company headquartered in Cupertino, California, in Silicon Valley."}]

[Output Type]
dict

[Output Type Explanations]
Next Thought and Action (dict)

[Action]
Get next Thought and Action

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```

Result
```yml
[Output] {"Thought": "The headquarters of Apple Computers is in Cupertino, California, in Silicon Valley.", "Action": "Finish 'Cupertino, California, Silicon Valley'"}
```

Returns `'Cupertino, California, Silicon Valley'` which is the correct answer.