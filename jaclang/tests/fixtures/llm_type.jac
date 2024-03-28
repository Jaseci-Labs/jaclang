obj 'outter'
Outer{
    has a: 'A': int  = 1;

    obj 'Person'
    Person {
        has name: 'Name' :str,
            dob: 'Date of Birth': str,
            age: 'Age': int = None;

    }

    can 'get_age'
    get_age(){
        # out=Person(name='Einstein') by llm(x='khjkh');
        return self.age;
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
            
        can 'get_age'
        get_age(){
        # out=Outer().Person(name='Einstein') by llm(x='khjkh');
        return self.age;
    }

    }

    can 'get_age'
    get_age(){
        out:int=Outer().Person(name='Einstein') by llm(x='khjkh');
        return self.age;
    }

}

with entry{
    llm='llm';
    person_obj:'Person object ':Person = Outer().Person(name='Einstein') by llm(x='khjkh');
    # Outer.a:'Person object ':Person = Outer().Person(name='Einstein') by llm(y=8);
    # person_obj:Person = Outer.Person(name='Einstein') by llm;
    # print(person_obj.dob);
}

