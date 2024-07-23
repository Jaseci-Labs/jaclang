
obj Calculator {
    """ Add multiple numbers """
    can add(x: float, *y: tuple) -> float {}

    """ Substract second value from the first value """
    can subtract(x: float, y: float) -> float {}

    """ Multiply two numbers """
    can multiply(x: float, y: float) -> float {}

    """ Divide first number by the second number """
    can divide(x: float, y: float) -> float {}
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
    print(cal.add(5, (10,11)));
    print(cal.subtract(5, 10));
    print(cal.multiply(5, 10));
    print(cal.divide(5, 10));
    print(adv_cal.power(5, 10));
    print(adv_cal.square_root(25));
    print(adv_cal.cube_root(27));
    print(adv_cal.remainder(10, 3));
    print(adv_cal.absolute(-5));
}
