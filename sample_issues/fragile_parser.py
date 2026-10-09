from collections.abc import Sequence


def parse_total(values: Sequence[str | int]) -> int:
    """Parse the first value in a non-empty sequence as an integer."""
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("values must be a sequence of strings or integers")
    if not values:
        raise ValueError("values must contain at least one item")

    value = values[0]
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise TypeError("the first value must be a string or integer")
    try:
        return int(value)
    except ValueError as error:
        raise ValueError("the first value must contain a valid integer") from error