'''Model'''
model llm {
    has model_name: "gpt-4",
        temperature: 0.7,
        do_sample: true;
}

'''Type'''
obj 'Person'
Person {
    has 'Name' name : String,
        'date of birth' dob : String,
        'Accomplishments' accomplishments : List[String];
}
with entry{
    Einstein = Person(name="Einstein") with llm;
}