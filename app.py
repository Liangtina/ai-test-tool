
import math
    def power(self, a, b):
        """Возведение числа a в степень b"""
        return a ** bdef main():
    calc = Calculator()
    print("Calculator Demo")
    print(f"5 + 3 = {calc.add(5, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"6 * 7 = {calc.multiply(6, 7)}")
    print(f"15 / 3 = {calc.divide(15, 3)}")
    print(f"2 ^ 3 = {calc.power(2, 3)}")  # Новая строка

if __name__ == "__main__":
    main()

import math

    def sqrt(self, a):
        """Квадратный корень числа"""
        if a < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return math.sqrt(a)
