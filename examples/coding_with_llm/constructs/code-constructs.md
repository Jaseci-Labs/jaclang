# Model
```python
model llm {
    model_name: "gpt-4";
    temperature: 0.7;
    do_sample: true;
}
```

# Function
```python
function 'Summarize the Accomplishments'
summarize ('Accomplishments' a: List[String]) -> 'Summary of the Accomplishments' summary: String Using llm

summarize(a=["Won Nobel Prize", "Discovered the Theory of Relativity"])
```

- Inputs to AOTT Raise
    - `[Information] = None`
    - `[Inputs and Input Type Information] = [('Accomplishments', 'List[String]', 'a', ["Won Nobel Prize", "Discovered the Theory of Relativity"])]`
    - `[Output Types] = [('String')]`
    - `[Output Type Exaplanations] = [('Summary of the Accomplishments', 'String', 'summary')]`
    - `[Action] = ('Summarize the Accomplishments')`
- Inputs to AOTT Raise --> AOTT Raise --> Meaning In
- Meaning In --> LLM --> Meaning Out
- Meaning Out --> AOTT Lower --> `Won the Nobel Prize for discovering the Theory of Relativity.`

# Type
```python
class 'Person'
Person {
    Variable 'Name' name : String
    Variable 'date of birth' dob : String
    Variable 'Accomplishments' accomplishments : List[String]
}
Einstein = Person(name="Einstein") by llm
```

- Inputs to AOTT Raise
    - `[Information] = None`
    - `[Inputs and Input Type Information] = [('Name', 'String', 'name', 'Einstein')]`
    - `[Output Types] = [('Person')]`
    - `[Output Type Exaplanations] = [('Person', 'Person', (('Name', 'String', 'name'), ('date of birth', 'String','dob'), ('Accomplishments', 'List[String]', 'accomplishments)]`
    - `[Action] = ('Create the Output Object fill the fields.')`
- Inputs to AOTT Raise --> AOTT Raise --> Meaning In
- Meaning In --> LLM --> Meaning Out
- Meaning Out --> AOTT Lower --> `Person(name="Einstein", dob=Filled by LLM, accomplishments=Filled by LLm)`

# Method
```
Class 'Person'
Person {
    Variable 'Name' name : String
    Variable 'Date of Birth' dob : String
    Variable 'Age' age : Int

    Method 'Calculate the Age of a Person'
    calculate ('Current Year' cur_year: Int) -> 'Calculated Age' calculated_age: Int Using llm {
        Self.age = calculated_age
    }
}
Object = Person(name="Einstein", dob="March 14, 1879")
Object.calculate(cur_year=2024)
```

- Inputs to AOTT Raise
    - `[Information] = [('Name', 'String', 'name', 'Einstein'), ('Date of Birth', 'String', 'dob', 'March 14, 1879')]`
    - `[Inputs and Input Type Information] = [('Current Year', 'Int', 'cur_year', 2024)]`
    - `[Output Types] = [('Int')]`
    - `[Output Type Exaplanations] = [('Calculated Age', 'Int', 'calculated_age')]`
    - `[Action] = ('Calculate the Age of a Person')`
- Inputs to AOTT Raise --> AOTT Raise --> Meaning In
- Meaning In --> LLM --> Meaning Out
- Meaning Out --> AOTT Lower --> `127`