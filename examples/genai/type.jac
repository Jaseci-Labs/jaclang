import:py from model, OpenAIModel, ClaudeModel;

model llm:ClaudeModel {
    model_name="claude-3-sonnet-20240229";
}

# model llm:OpenAIModel {
#     model_name="gpt-4";
# }

obj 'Person'
Person {
    has name: 'Name of the Person': str,
        dob: 'Date of Birth': str,
        age: 'Age of the Person': int;
}

# with entry {
#     einstein: 'Einstein Object': Person = Person(name="Albert Einstein") by llm();
#     print(einstein.dob);
# }


obj 'University'
University {
    has name: 'Name of the University': str,
        location: 'Location of the University': str;

    obj 'Department'
    Department {
        has name: 'Name of the Department': str,
            head: 'Head of the Department': Person;
    }
}

with entry {
    mit: 'MIT University': University = University(name="University of Michigan", location="Ann Arbor, Michigan");
    cs_department: 'Computer Science Department': University.Department = University.Department(name="Computer Science")
    by llm(incl_info=(mit), context=["Jason Mars is the head of the department.", "He is now 30 years old.", "Now is 2024"]);
    
    print(cs_department);
    print(cs_department.head);
}