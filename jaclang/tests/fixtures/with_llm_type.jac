obj model {
    can init(output_str: str) {
        self.output_str = output_str;
    }
    can __infer__(meaning_in: str, **kwargs: dict) {
        return f"[Output] {self.output_str}";
    }
}
glob llm1 = model(output_str="Person(name='Albert Einstein', dob='14/03/1879', age=76)");

obj 'Person'
Person {
    has name: 'Name of the Person': str,
        dob: 'Date of Birth': str,
        age: 'Age of the Person': int;
}

with entry {
    einstein: 'Einstein Object': Person = Person(name="Albert Einstein") by llm1();
    print(einstein.dob); #14/03/1879
}

glob llm2 = model(output_str="University.Department(name='Computer Science', head=Person(name='Jason Mars', dob='1994-01-01', age=30))");

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

obj 'Country'
country {
    can create_univeristy(location: str) {
        university: "New Univerisity": University = University(location=location)
        by llm1(context=["Choose a tamil name"]);
    }
}

# with entry {
#     mit: 'MIT University': University = University(name="University of Michigan", location="Ann Arbor, Michigan");
#     cs_department: 'Computer Science Department': University.Department = mit.Department(name="Computer Science")
#     by llm2(incl_info=(mit), context=["Jason Mars is the head of the department.", "He is now 30 years old.", "Now is 2024"]);
#     print(cs_department.head); # Person(name='Jason Mars', dob='1994-01-01', age=30)
# }