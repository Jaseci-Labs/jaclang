obj model {
    can __infer__(meaning_in: str, **kwargs: dict) {
        print(kwargs);
        print(meaning_in);
        return "[Output] Something";
    }
}
glob llm = model();

glob emoji_examples: 'Examples of Text to Emoji': list[dict[str, str]] = [
    {
         "input": "I love tp drink pina coladas",
<<<<<<< HEAD
         "output": "fhff"
    },
    {
        "input": "Mime Person",
        "output": "fgdfgdfgdf"
=======
         "output": "{:cocktail:} {:beach_with_umbrella:}"
    },
    {
        "input": "Mime Person",
        "output": "{:person_miming:}"
>>>>>>> 11095feb51f0466feb663be5115e5d7a97fe237a
    }

];

can 'Get Emoji Representation'
get_emoji(input: 'Text Input': str) -> 'Emoji Representation': str by llm(temperature=0.7,  incl_info=(emoji_examples),excl_info=());

with entry {
    print(get_emoji('Lets move to paris'));
}