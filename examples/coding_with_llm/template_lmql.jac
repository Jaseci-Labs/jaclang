# """
# Write a summary of Bruno Mars, the singer:
# {{
#     "name": "[STRING_VALUE]",
#     "age": [INT_VALUE],
#     "top_songs": [[
#         "[STRING_VALUE]",
#         "[STRING_VALUE]"
#     ]]
# }}
# """ where STOPS_BEFORE(STRING_VALUE, '"') and \
#           INT(INT_VALUE) and len(TOKENS(INT_VALUE)) < 2

include:plugin openai;
             
model llm:openai {
    has model_name: "openai/gpt-4",
        temperature: 0.7,
        do_sample: true;
}

obj 'Person'
Person {
    has name: 'Name of the person' str,
        age: 'age' str,
        top_songs: 'his/her top_songs' list[str,str];
}

with entry{
    Bruno_Mars = Person(name="Bruno Mars") with llm;
    print(f"{Bruno_Mars.name} age is {Bruno_Mars.age}. His top_songs are {Bruno_Mars.top_songs}.");
}


