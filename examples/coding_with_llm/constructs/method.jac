include:plugin openai;

model llm:openai {
    has model_name: "gpt-4",
        temperature: 0.7,
        do_sample: true;
}

obj 'Person'
Person {
    has name: 'Name' str,
        dob: 'Date of Birth' str,
        age: 'Age' int = None;

    can 'Calculate the Age of a Person'
    calculate (cur_year: 'Current Year' int) -> 'Calculated Age' int with llm;
}
with entry{
    Einstein = Person(name="Einstein", dob="1879-03-14");
    age = Einstein.calculate(cur_year=2024);
    Einstein.age = age;
    print(Einstein.age);
}