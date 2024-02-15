include:plugin openai;

model llm:openai {
    has model_name: "gpt-4",
        temperature: 0.7,
        do_sample: true;
}

obj 'Person'
Person {
    has name: 'Name' str,
        dob: 'date of birth' str,
        accomplishments: 'Accomplishments' list[str];
}

with entry{
    Einstein = Person(name="Einstein") with llm;
    print(f"{Einstein.name} was born on {Einstein.dob}. His accoomplishments includes {Einstein.accomplishments}.");
}