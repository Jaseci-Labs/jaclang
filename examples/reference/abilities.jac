
obj Calculator {
    can add(x: float, y: tuple) -> float;
    can substract(x: float, y: float) -> float;
    can multiply(x: float, y: float) -> float;
    can divide(x: float, y: float) -> float;
}

obj BasicCalculator :Calculator: {
    can add(x: float, y: tuple) -> float {
        return (x + sum(y));
    }
    can substract(x: float, y: float) -> float {
        return (x - y);
    }
    can multiply(x: float, y: float) -> float {
        return (x * y);
    }
    can divide(x: float, y: float) -> float {
        return (x / y);
    }
}

obj AdvancedCalculator:BasicCalculator{
    
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
    advcal = AdvancedCalculator();
    print(cal.add(1, (2, 3, 4)));
    print(cal.substract(10, 5));
    print(cal.multiply(2, 3));
    print(cal.divide(10, 2));
    print(advcal.power(2, 3));

}
