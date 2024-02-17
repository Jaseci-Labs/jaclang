Creating the Graph of a Family
```python
passage = "Rich's daughter Christine made dinner for her sister Kim. Beth went to her brother Rich's birthday party. Anne went shopping with her sister Kim.";
graph = create_family(passage);
```
1st Iteration
```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed. 

[Information]
Example Family Graph (graph) example_family_graph = {john = person(name = 'John'), jane = person(name = 'Jane'), john -[relationship(relation = 'husband')]-> jane}
Person (person) ((Name (str) (name)))
Relationship (relationship) ((Relation (str) (relation)))

[Inputs and Input Type Information]
Passage describing the Family (str) (passage) = "Rich's daughter Christine made dinner for her sister Kim. Beth went to her brother Rich's birthday party. Anne went shopping with her sister Kim."

[Output Type]
graph

[Output Type Explanations]
Graph Representing the Family (graph)

[Action]
Create Family Graph

Reason and return the output result(s) only, adhering to the provided Type in the following format

[Reasoning] <Reason>
[Output] <Result>
```

Result
```yml
[Reasoning] From the given passage, we can understand the relationships between the characters as follows: Rich is father to Christine and Kim. Beth is Rich's sister. Anne is Kim's sister.
[Output] {rich = person(name = 'Rich'), christine = person(name = 'Christine'), kim = person(name = 'Kim'), beth = person(name = 'Beth'), anne = person(name = 'Anne'), rich -[relationship(relation = 'father')]-> christine, rich -[relationship(relation = 'father')]-> kim, beth -[relationship(relation = 'sister')]-> rich, anne -[relationship(relation = 'sister')]-> kim}
```

Quering the graph
```python
query = "Rich is Annie's?";
answer = query_family(graph, query);
```
1st Iteration
```yml
[System Prompt]
This is an operation you must perform and return the output values. Neither, the methodology, extra sentences nor the code are not needed. 

[Information]
None

[Inputs and Input Type Information]
Graph Representing the Family (graph) family_graph = {rich = person(name = 'Rich'), christine = person(name = 'Christine'), kim = person(name = 'Kim'), beth = person(name = 'Beth'), anne = person(name = 'Anne'), rich -[relationship(relation = 'father')]-> christine, rich -[relationship(relation = 'father')]-> kim, beth -[relationship(relation = 'sister')]-> rich, anne -[relationship(relation = 'sister')]-> kim}
Question (str) question = "Rich is Annie's?"

[Output Type]
str

[Output Type Explanations]
Answer (str)

[Action]
Answer Question about the Family

Reason and return the output result(s) only, adhering to the provided Type in the following format

[Reasoning] <Reason>
[Output] <Result>
```

Result
```yml
[Reasoning] Looking at the family graph, there is no direct relationship between Rich and Anne. Rich is a father to Christine and Kim, and has a sister named Beth. Anne is only related to Kim as a sister. Since Anne is not stated to be related to any of Rich's children, we can't infer a relationship between Rich and Anne based on this graph. 
[Output] Not related
```
