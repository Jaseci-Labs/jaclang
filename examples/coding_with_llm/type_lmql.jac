# import lmql
# from dataclasses import dataclass

# @dataclass
# class Employer:
#     employer_name: str
#     location: str

# @dataclass
# class Person:
#     name: str
#     age: int
#     employer: Employer
#     job: str

# # use type constraints to generated (type-safe) structured data
# "Alice is a 21 years old and works as an engineer at LMQL Inc in Zurich, Switzerland.\n"
# "Structured: [PERSON_DATA]\n" where type(PERSON_DATA) is Person

# # the resulting object is directly accessible as a Python object
# "Their name is {PERSON_DATA.name} and she works in {PERSON_DATA.employer.location}."

model llm:openai {
    has model_name: "gpt-3.5-turbo",
        temperature: 0.7,
        do_sample: true;
}

obj 'Employer'
Employer {
    has employer_name: 'Employer Name' str,
        location: 'Location' str;
}

obj 'Person'
Person {
    has name: 'Name' str,
        age: 'Age' int,
        employer: 'Employer' Employer,
        job: 'Job' str;
}

with entry {
    info: "Person's Information" str = "Alice is a 21 years old and works as an engineer at LMQL Inc in Zurich, Switzerland.";
    person = Person with llm(info=(info));
    print(f"Their name is {person.name} and she works in {person.employer.location}.")
}