import:py math;

glob RAD = 5;
glob DIA = 10;

walker decorator_walk {
    can hash(func: Any) {
        can inner(a: Any) {
            print(("#" * 20));
            func(a);
            print(("#" * 20));
        }
        return inner;
    }

    can exclaim(func: Any) {
        can inner(b: Any) {
            print(("!" * 20));
            func(b);
            print(("!" * 20));
        }
        return inner;
    }

    can tilde(func: Any) {
        can inner(c: Any) {
            print(("~" * 20));
            func(c);
            print(("~" * 20));
        }
        return inner;
    }

    can greeter(name: Any) {
        print("Hello, " + name + "!");
    }

    # Entry point for the walker
    can start with entry {
        # Apply decorators to greeter
        decorated_greeter = hash(exclaim(tilde(greeter)));

        # Call the decorated greeter function
        decorated_greeter("World");
    }
}

with entry {
    root spawn decorator_walk();
}
