from abc import ABC, abstractmethod


class Calculator(ABC):
    """
    Abstract Base Class for basic calculator operations.
    """

    @abstractmethod
    def add(self, x: float, y: tuple) -> float:
        """
        Add two numbers.

        :param x: First number
        :param y: Second number
        :return: The sum of x and y
        """
        pass

    @abstractmethod
    def subtract(self, x: float, y: float) -> float:
        """
        Subtract two numbers.

        :param x: First number
        :param y: Second number
        :return: The difference of x and y
        """
        pass

    @abstractmethod
    def multiply(self, x: float, y: float) -> float:
        """
        Multiply two numbers.

        :param x: First number
        :param y: Second number
        :return: The product of x and y
        """
        pass

    @abstractmethod
    def divide(self, x: float, y: float) -> float:
        """
        Divide two numbers.

        :param x: First number
        :param y: Second number
        :return: The quotient of x and y
        """
        pass


class BasicCalculator(Calculator):
    """
    Basic calculator implementation.
    """

    def add(self, x: float, y: tuple) -> float:
        return x + sum(y)

    def subtract(self, x: float, y: float) -> float:
        return x - y

    def multiply(self, x: float, y: float) -> float:
        return x * y

    def divide(self, x: float, y: float) -> float:
        return x / y


class AdvanceCalculator(BasicCalculator):
    """
    Advance calculator implementation.
    """

    def power(self, x: float, y: float) -> float:
        """
        Raise x to the power of y.
        """
        return x**y

    def square_root(self, x: float) -> float:
        """
        Compute the square root of x.
        """
        return x**0.5

    def cube_root(self, x: float) -> float:
        """
        Compute the cube root of x.
        """
        return x ** (1 / 3)

    def remainder(self, x: float, y: float) -> float:
        """
        Compute the remainder of x divided by y.
        """
        return x % y

    def absolute(self, x: float) -> float:
        """
        Compute the absolute value of x.
        """
        return abs(x)


cal = BasicCalculator()
adv_cal = AdvanceCalculator()
print(cal.add(5, (10,11)))
print(cal.subtract(5, 10))
print(cal.multiply(5, 10))
print(cal.divide(5, 10))
print(adv_cal.power(5, 10))
print(adv_cal.square_root(25))
print(adv_cal.cube_root(27))
print(adv_cal.remainder(10, 3))
print(adv_cal.absolute(-5))
