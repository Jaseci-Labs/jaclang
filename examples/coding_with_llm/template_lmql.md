Jac
```python
bruno_mars = Singer(name="Bruno Mars") with llm;
```
```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed. 

[Information]
Name of the Singer (str) (name) = "Bruno Mars"

[Inputs and Input Type Information]
None

[Output Type]
Singer

[Output Type Explanations]
Singer (Singer) (Name of the Singer (str) name, Age (int) age, His/Her's Top 2 Songs (list[str]) top_songs)

[Action]
Create the Output Object. fill the fields. If there is nested object, fill the fields of the nested object as well.

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```

Result
```yml
[Output] Singer(name = "Bruno Mars", age = 35, top_songs = ['Just the Way You Are', 'Grenade'])
```
