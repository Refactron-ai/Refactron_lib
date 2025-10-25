"""
A simple, clean Python example for CI testing.

This file has minimal issues and won't trigger critical errors.
"""


def add_numbers(a: int, b: int) -> int:
    """Add two numbers and return the result."""
    return a + b


def multiply_numbers(x: int, y: int) -> int:
    """Multiply two numbers and return the result."""
    return x * y


def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"


def main() -> None:
    """Main function demonstrating simple operations."""
    result1 = add_numbers(5, 3)
    result2 = multiply_numbers(4, 7)
    message = greet("World")

    print(f"Addition: {result1}")
    print(f"Multiplication: {result2}")
    print(message)


if __name__ == "__main__":
    main()
