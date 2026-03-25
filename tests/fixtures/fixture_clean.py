"""A clean module with zero code issues.

This fixture exists as a negative control: analyzers and autofix
should find nothing to report or change.
"""

from typing import List

__all__ = ["fibonacci"]


def fibonacci(n: int) -> List[int]:
    """Return the first *n* Fibonacci numbers.

    Args:
        n: How many numbers to generate.

    Returns:
        A list of Fibonacci numbers.
    """
    if n <= 0:
        return []

    sequence: List[int] = [0]
    if n == 1:
        return sequence

    sequence.append(1)
    for _ in range(2, n):
        sequence.append(sequence[-1] + sequence[-2])

    return sequence
