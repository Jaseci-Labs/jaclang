obj model {
    can __infer__(meaning_in: str, **kwargs: dict) {
        print(meaning_in);
        return "[Output] Something";
    }
}
glob llm = model();

obj 'outter'
Outer{
    has a: 'A': int  = 1;

    obj 'Person'
    Person {
        has name: 'Name' :str,
            dob: 'Date of Birth': str,
            age: 'Age': int = None;

    }

}
obj 'outter'
Outer2{
    has a: 'A': int  = 1;

    obj 'Person'
    Person2 {
        has name: 'Name' :str,
            dob: 'Date of Birth': str,
            age: 'Age': int = None;
            
        # can 'get_age'
        # get_age(){
        # out=Outer().Person(name='Einstein') by llm(x='khjkh');
    #     return out;
    # }

    }

    # can 'get_age'
    # get_age(){
        # out:int=Outer().Person(name='Einstein') by llm(x='khjkh');
    #     return out;
    # }

}

with entry{
    # person_obj:'Person object ':Person = Person(name='Einstein',a=9) by llm(x='khjkh');
    # person_obj:'Person object ':Person = Outer().Person(name='Einstein',a=9) by llm(x='khjkh');
    person_obj:'Person object ':Person = Outer().Person(name='Einstein') by llm(temperature=0.2);
    # Outer.a:'Person object ':Person = Outer().Person(name='Einstein') by llm(y=8);
    # person_obj:Person = Outer.Person(name='Einstein') by llm;
    # print(person_obj.dob);
}

