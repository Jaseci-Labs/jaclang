obj 'outter'
Outer{
    has a: 'A': int = 1;

    obj 'Person'
    Person {
        has name: 'Name' :str,
            dob: 'Date of Birth': str,
            age: 'Age': int = None;
    }
}

with entry{

    person_obj:'Person object ':Person = Outer().Person(name='Einstein') by llm;
    # person_obj=_Jac.with_llm_type(file_loc=__file__, model='', scope='',  inputs=[]) 

    Outer.a:'Person object ':Person = Outer().Person(name='Einstein') by llm;
    # person_obj:Person = Outer.Person(name='Einstein') by llm;
    # print(person_obj.dob);
}

