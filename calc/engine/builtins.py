import math

SAFE_NAMES = {
    # trig (radians)
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "atan2": math.atan2,
    # trig (degrees)
    "sind": lambda x: math.sin(math.radians(x)),
    "cosd": lambda x: math.cos(math.radians(x)),
    "tand": lambda x: math.tan(math.radians(x)),
    # hyperbolic
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    # logs & exp
    "log": math.log, "log2": math.log2, "log10": math.log10,
    "ln": math.log, "exp": math.exp,
    # powers & roots
    "sqrt": math.sqrt, "pow": math.pow,
    # rounding
    "abs": abs, "round": round, "floor": math.floor, "ceil": math.ceil,
    # misc
    "factorial": math.factorial, "gcd": math.gcd,
    "degrees": math.degrees, "radians": math.radians,
    # constants
    "pi": math.pi, "e": math.e, "tau": math.tau, "inf": math.inf,
}
