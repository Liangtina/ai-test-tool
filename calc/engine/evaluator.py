from calc.engine.builtins import SAFE_NAMES


def evaluate(expr: str, extra_names: dict = None) -> tuple[str, bool]:
    """
    Evaluate a math expression safely.
    Returns (result_string, is_error).
    """
    namespace = dict(SAFE_NAMES)
    if extra_names:
        namespace.update(extra_names)
    try:
        result = eval(expr, {"__builtins__": {}}, namespace)
        return str(result), False
    except ZeroDivisionError:
        return "Error: Division by zero", True
    except ValueError as err:
        return f"Error: {err}", True
    except NameError as err:
        return f"Error: {err}", True
    except Exception as err:
        return f"Error: {err}", True
