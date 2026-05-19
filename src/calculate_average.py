def calculate_average(values: list[float]) -> float:
    """Return the arithmetic mean of values, or 0 if the list is empty."""
    if not values:
        return 0
    return sum(values) / len(values)
