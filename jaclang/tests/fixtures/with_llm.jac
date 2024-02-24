"""With LLM Sytax Test"""

obj model {
    can __infer__(**kwargs: dict) {
        return(kwargs);
    }
}
glob llm = model();

can something(c: str) with llm(a="Hello", b="World");
with entry {
    print(something('test'));
}

# can get_personality() with llm(a=4, b=5);

# with entry {
#     get_personality();
# }