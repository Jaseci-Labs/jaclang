model llm:openai {
    has model_name: "gpt-3.5-turbo",
        temperature: 0.7,
        do_sample: true;
}

glob examples: "Examples of English words translated to french" dict[str,str] = { 
    "sea otter": "loutre de mer",
    "peppermint": "menthe poivrée",
    "plush giraffe": "girafe en peluche"
};


can 'Translate English to French'
translate(english_word: 'English Word' str)-> 'French Word' str with llm;

with entry {
    print(translate("cheese"));
}
 