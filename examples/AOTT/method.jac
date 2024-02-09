include:plugin openai;

model llm:openai {
    has model_name: "gpt-4",
        temperature: 0.7,
        do_sample: true;
}

obj 'Person'
Person {
    has 'Name' name:str,
        'Date of Birth' dob:str,
        'Age' age:int = None;

    can 'Calculate the Age of a Person'
    calculate ('Current Year' cur_year:int) -> 'Calculated Age' calculated_age:int with llm {
        self.age = calculated_age;
    }
}
with entry{
    Einstein = Person(name="Einstein", dob="1879-03-14");
    Einstein.calculate(cur_year=2024);
    print(Einstein.age);
}