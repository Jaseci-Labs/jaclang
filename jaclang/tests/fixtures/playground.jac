# let : priv a = 5;

# glob : pub X = 10;

# glob : protect y = 15;

# glob z = 20;

obj Divider {
    can divide(x: float, y: float) -> float {
        return (x / y);
    }
    obj dd{
        can hh() -> int {
            return 10;
        }

    }
}

with entry {
    div = Divider();
    print(div.divide(10, 2));
    print(div.dd().hh());
    # print(a, X, y, z);
    # print(X);

}

obj Animal {
    has :pub name: str;
    has :priv age: int;
    has :protect sound: str;

    can :pub introduce() {
        return "Hello, I am " + self.name + ". ";
    }

    can :protect makeSound(){
        return self.sound;
    }
}

obj Dog: Animal: {
    has :pub breed: str;

    can <init>(name: str, age: int, sound: str, breed: str) {
        self.name = name;
        self.age = age;
        self.sound = sound;
        self.breed = breed;
    }

    can :pub bark() {
        return "Woof! Woof!";
    }

    can :protect makeSound() {
        return "The dog says: " + <super>.makeSound();
    }
}

with entry {
     myDog = Dog(name= "Buddy", age= 3, sound= "Woof", breed= "Golden Retriever");

    # Accessing public attributes and methods
    print( " Name: " + myDog.name );
    print( " Breed: " + myDog.breed );
    print( myDog.introduce() );
    print( myDog.bark() );

    # Attempting to access private and protected attributes
    # Uncommenting the following lines would result in a compilation error
    print( " Age: " + f'{myDog.age}');
    print( " Sound: " + myDog.sound);

    # Accessing protected method
    # no error will araise as it is a protected method and can be accessed by the subclass
    print( " Sound: " + myDog.makeSound());
}
