# argmax
# "Pick the odd word out: skirt, dress, pen, jacket.\n"
# "skirt is clothing, dress is clothing, pen is an object, jacket is clothing.\n"
# "So the odd one is pen.\n\n"
# "Pick the odd word out: Spain, France, German, England, Singapore.\n"
# "Spain is a country, France is a country, German is a language, ...\n"
# "So the odd one is German.\n\n"
# "Pick the odd word out: {OPTIONS}\n"
# "[REASONING]"
# "[RESULT]"
# from "EleutherAI/gpt-j-6B"
# where
# not "\n" in REASONING and not "Pick" in REASONING and
# stops_at(REASONING, "Pick the odd word") and stops_at(REASONING, "\n") and
# stops_at(REASONING, "So the odd one") and stops_at(REASONING, ".") and len(WORDS(REASONING)) < 40
# distribute
# RESULT over OPTIONS.split(", ")

model llm:openai {
    has model_name: "gpt-3.5-turbo",
        temperature: 0.7,
        do_sample: true;
}

glob examples: 'Examples for Picking Odd Word out' list[dict] = [
    {
        "OPTIONS": ["skirt", "dress", "pen", "jacket"],
        "REASONING": "skirt is clothing, dress is clothing, pen is an object, jacket is clothing.",
        "RESULT": "pen"
    },
    {
        "OPTIONS": ["Spain", "France", "German", "England", "Singapore"],
        "REASONING": "Spain is a country, France is a country, German is a language, ...",
        "RESULT": "German"
    }
];

can 'Pick the Odd word out'
pick_odd_word_out_v1(options: 'Options to pick from' list[str]) -> 'Result' str by llm(reason=True);

can 'Pick the Odd word out'
pick_odd_word_out_v2(options: 'Options to pick from' list[str]) -> 'OPTIONS, REASONING & RESULT' dict by llm;

with entry {
    options = ["Bentley", "Ferrari", "Lamborghini", "Casio", "Toyota"];
    print(pick_odd_word_out_v1(options)); # Casio
    print(pick_odd_word_out_v2(options)); # {"OPTIONS": ["Bentley", "Ferrari", "Lamborghini", "Casio", "Toyota"], "REASONING": "Bentley is a car, Ferrari is a car, Lamborghini is a car, Casio is a watch, Toyota is a car.", "RESULT": "Casio"}
}