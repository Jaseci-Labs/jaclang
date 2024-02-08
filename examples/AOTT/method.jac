'''Method'''
obj 'Person'
Person {
    has   'Name' name : String,
          'Date of Birth' dob : String,
          'Age' age : Int;

    can 'Calculate the Age of a Person'
    calculate ('Current Year' cur_year: Int) -> 'Calculated Age' calculated_age: Int Using llm {
        self.age = calculated_age;
    }
}
with entry{
    Einstein = Person(name="Einstein", dob="March 14, 1879",age=78);
    Einstein.calculate(cur_year=2024);
}