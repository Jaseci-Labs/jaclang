```jac
joke = joke_generate();
```

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed.

[Information]
Jokes with Punchlines (list[dict]) (jokes): [{"joke": "How does a penguin build its house?", "punchline": "Igloos it together."},{"joke": "Which knight invented King Arthur's Round Table?", "punchline": "Sir Cumference."}]

[Inputs and Input Type Information]
None

[Output Type]
str

[Output Type Explanations]
Joke (str)

[Action]
Generate only a new joke

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```

Result
```yml
[Output] Why don't scientists trust atoms?
```

-----
```jac
punchline = punchline_generate(joke);
```

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed.

[Information]
Jokes with Punchlines (list) (jokes): ["Q: How does a penguin build its house?\nA: Igloos it together.", "Q: Which knight invented King Arthur's Round Table?\nA: Sir Cumference."]

[Inputs and Input Type Information]
Joke (str) (joke) = "Why don't scientists trust atoms?"

[Output Type]
str

[Output Type Explanations]
Punchline (str)

[Action]
Generate the Punchline for the Joke

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```

Result
```yml
[Output] "Because they make up everything!"
```

-----
```jac
joke_punchline = generate_joke_punchline();
```

```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed.

[Information]
Jokes with Punchlines (list[dict]) (jokes): [{"joke": "How does a penguin build its house?", "punchline": "Igloos it together."},{"joke": "Which knight invented King Arthur's Round Table?", "punchline": "Sir Cumference."}]

[Inputs and Input Type Information]
None

[Output Type]
dict

[Output Type Explanations]
Joke with Punchline (dict)

[Action]
Generate a Joke with Punchline

Generate and return the output result(s) only, adhering to the provided Type in the following format

[Output] <result>
```

Result
```yml
[Output] {"joke": "Why don't scientists trust atoms?", "punchline": "Because they make up everything."}
```