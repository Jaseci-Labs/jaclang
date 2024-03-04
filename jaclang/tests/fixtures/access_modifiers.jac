# obj Animal {
#     has :pub name: str;
#     has :priv age: int;
#     has :protect sound: str;

#     can :pub introduce() {
#         return "Hello, I am " + self.name + ". ";
#     }

#     can :protect makeSound(){
#         return self.sound;
#     }
# }

# obj Dog: Animal: {
#     has :pub breed: str;
    
#     can init(name: str, age: int, sound: str, breed: str) {
#         self.name = name;
#         self.age = age;
#         self.sound = sound;
#         self.breed = breed;
#     }

#     can :pub bark() {
#         return "Woof! Woof!";
#     }

#     can :protect makeSound() {
#         return "The dog says: " + super.makeSound();
#     }
# }

# with entry {
    #  myDog = Dog(name= "Buddy", age= 3, sound= "Woof", breed= "Golden Retriever");

    # # Accessing public attributes and methods
    # print( " Name: " + myDog.name );
    # print( " Breed: " + myDog.breed );
    # print( myDog.introduce() );
    # print( myDog.bark() );

    # Attempting to access private and protected attributes
    # Uncommenting the following lines would result in a compilation error
    # print( " Age: " + f'{myDog.age}');
    # print( " Sound: " + myDog.sound);

    # Accessing protected method
    # no error will araise as it is a protected method and can be accessed by the subclass
    # print( " Sound: " + myDog.makeSound()); 
# }


#lets create a person 
# obj Person {
#     has :pub name: str;
#     has :priv age: int;
#     has :protect sound: str='meow';

   
    
# }
# with entry {
#     myPerson = Person(name= "Buddy", age= 3);
#     print( " Name: " + myPerson.name );
#     print( " Age: " + f'{myPerson.age}');
# }




include:jac check;
glob b: int=5;

with entry{
    xx=a; 
    print(b);
}






#simple class and object

# with entry {
#     obj Person {
#     has :pub name: str;
#     has :priv age: int;
 
# }
#     myPerson = Person(name= "Buddy", age= 3);
#     print( " Name: " + myPerson.name );
#     print( " Age: " + f'{myPerson.age}');
# }