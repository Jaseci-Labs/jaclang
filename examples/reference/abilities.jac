
obj Calculator {
    """ Add multiple numbers """
    can add(x: float, *y: tuple) -> float abs;

    """ Substract second value from the first value """
    can subtract(x: float, y: float) -> float abs;

    """ Multiply two numbers """
    can multiply(x: float, y: float) -> float abs;

    """ Divide first number by the second number """
    can divide(x: float, y: float) -> float abs;

    """ Check if a number is positive """
    static can is_positive(number: float) -> bool{
        return number > 0;
    }
}


obj BasicCalculator :Calculator: {
    can add(x: float, y: tuple) -> float {
        return (x + sum(y));
    }

    can subtract(x: float, y: float) -> float {
        return (x - y);
    }

    can multiply(x: float, y: float) -> float {
        return (x * y);
    }

    can divide(x: float, y: float) -> float {
        return (x / y);
    }
}

obj AdvancedCalculator:BasicCalculator: {
    can power(x: float, y: float) -> float {
        return (x ** y);
        }

    can square_root(x: float) -> float {
        return (x ** 0.5);
    }

    can cube_root(x: float) -> float {
        return (x ** (1/3));
    }

    can remainder(x: float, y: float) -> float {
        return (x % y);
    }

    can absolute(x: float) -> float {
        return (abs(x));
    }
}

with entry {
    cal = BasicCalculator();
    adv_cal = AdvancedCalculator();
    # Perform operations using BasicCalculator
    print("Basic Calculator Operations:");
    print("Addition:", cal.add(5, (10,11)));
    print("Subtraction:", cal.subtract(5, 10));
    print("Multiplication:", cal.multiply(5, 10));
    print("Division:",cal.divide(5, 10));

    # Perform operations using AdvanceCalculator
    print("\nAdvance Calculator Operations:");
    print("Power:", adv_cal.power(5, 10));
    print("Square Root:",adv_cal.square_root(25));
    print("Cube Root:", adv_cal.cube_root(27));
    print("Remainder:", adv_cal.remainder(10, 3));
    print("Absolute Value:", adv_cal.absolute(-5));

    # Use the static method from the Calculator class
    print("\nStatic Method Check:");
    print("Is 10 positive?", Calculator.is_positive(10));
    print("Is -5 positive?", Calculator.is_positive(-5));
}
