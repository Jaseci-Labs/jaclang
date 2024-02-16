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

obj 'Singer'
Singer {
    has name: 'Name of the Singer' str,
        age: 'Age' int,
        top_songs: "His/Her's Top 2 Songs" list[str];
}

with entry{
    bruno_mars = Singer(name="Bruno Mars") with llm;
    print(f"{bruno_mars.name} is {bruno_mars.age} years old. His top 2 songs are {bruno_mars.top_songs}.");
}


