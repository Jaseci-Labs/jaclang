# Passage : Rich's daughter Christine made dinner for her sister Kim. Beth went to her brother Rich's birthday
# party. Anne went shopping with her sister Kim.
# Graph: <Graph that represents the passage>
# Query: Rich is Annies?
# Answer: Father

model llm:openai {
    has model_name: "gpt-4",
        temperature: 1.0,
        do_sample: true;
}

node 'Person' 
person {
    has name: 'Name' str;
}

edge 'Relationship' 
relationship {
    has relation: 'Relation' str;
}

graph 'Example Family Graph'
example_family_graph {
    john : person = person(name = 'John');
    jane : person = person(name = 'Jane');
    john -[relationship(relation = 'husband')]-> jane;
}

can 'Create Family Representation'
create_family (passage : 'Passage describing the Family' str) -> 'Graph Representing the Family' graph with llm(info=(example_family_graph));

can 'Answer Question about the Family'
query_family (family_graph : 'Graph Representing the Family' graph, question : 'Question' str) -> 'Answer' str with llm;

with entry {
    passage = "Rich's daughter Christine made dinner for her sister Kim. Beth went to her brother Rich's birthday party. Anne went shopping with her sister Kim.";
    graph = create_family(passage);
    query = "Rich is Annie's?";
    answer = query_family(graph, query);
    print(answer);
}