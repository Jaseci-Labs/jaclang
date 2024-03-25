# argmax
#     """A list of good dad jokes. A indicates the punchline
#     Q: How does a penguin build its house?
#     A: Igloos it together.
#     Q: Which knight invented King Arthur's Round Table?
#     A: Sir Cumference.
#     Q:[JOKE]
#     A:[PUNCHLINE]"""
# from
#     "openai/text-davinci-003"
# where
#     len(JOKE) < 120 and
#     STOPS_AT(JOKE, "?") and
#     STOPS_AT(PUNCHLINE, "\n") and
#     len(PUNCHLINE) > 1

model llm:openai {
    has model_name: "gpt-4",
        temperature: 0.7,
        do_sample: true;
}

obj "A list of good dad jokes. A indicates the punchline"
JokeList {
    has jokes: 'Jokes with Punchlines' list[dict] = [
        {
            "joke": "How does a penguin build its house?",
            "punchline": "Igloos it together."
        },
        {
            "joke": "Which knight invented King Arthur's Round Table?",
            "punchline": "Sir Cumference."
        }
    ];

    can 'Generate only a new joke'
    joke_generate -> 'Joke' str by llm(max_length=120);
    can 'Generate the Punchline for the Joke'
    punchline_generate (joke: 'Joke' str) -> 'Punchline' str by llm(end_at="\n");

    can generate {
        joke = joke_generate();
        punchline = punchline_generate(joke);
        jokes.append({
            "joke": joke,
            "punchline": punchline
        });
    }
}

obj "A list of good dad jokes. A indicates the punchline"
JokeList {
    has jokes: 'Jokes with Punchlines' list[dict] = [
        {
            "joke": "How does a penguin build its house?",
            "punchline": "Igloos it together."
        },
        {
            "joke": "Which knight invented King Arthur's Round Table?",
            "punchline": "Sir Cumference."
        }
    ];

    can 'Generate a Joke with Punchline'
    generate_joke_punchline -> 'Joke with Punchline' dict by llm;

    can generate {
        joke_punchline = generate_joke_punchline();
        jokes.append(joke_punchline);
    }
}