"""
Example: Error Handling Best Practices

This example demonstrates common error handling patterns
and how to improve them.
"""

import time
from typing import Callable, TypeVar

T = TypeVar("T")


# ❌ BAD: Generic exception catching
def bad_file_reader(filename):
    try:
        with open(filename, "r") as f:
            return f.read()
    except Exception:  # Too broad!
        return None


# ❌ BAD: Swallowing exceptions
def bad_process_data(data):
    try:
        result = int(data) * 2
        return result
    except Exception:
        pass  # Silent failure


# ❌ BAD: Using exceptions for flow control
def bad_number_checker(value):
    try:
        int(value)
        return True
    except Exception:
        return False


# ✅ GOOD: Specific exception handling
def good_file_reader(filename):
    """Read file contents with proper error handling."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        return None
    except PermissionError:
        print(f"Error: Permission denied for '{filename}'")
        return None
    except IOError as e:
        print(f"Error reading file: {e}")
        return None


# ✅ GOOD: Proper exception handling and logging
def good_process_data(data):
    """Process data with informative error messages."""
    try:
        result = int(data) * 2
        return result
    except ValueError as e:
        raise ValueError(f"Invalid data format: {data}. Expected integer.") from e
    except TypeError as e:
        raise TypeError(f"Data must be convertible to int, got {type(data)}") from e


# ✅ GOOD: Using appropriate checks instead of exceptions
def good_number_checker(value):
    """Check if value can be converted to integer."""
    if isinstance(value, int):
        return True
    if isinstance(value, str):
        return value.isdigit() or (value.startswith("-") and value[1:].isdigit())
    return False


# ✅ GOOD: Context manager for resource cleanup
class DatabaseConnection:
    """Example database connection with proper cleanup."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None

    def __enter__(self):
        """Establish connection."""
        try:
            # Simulated connection
            print(f"Connecting to {self.connection_string}")
            self.connection = {"connected": True}
            return self
        except Exception as e:
            raise ConnectionError(f"Failed to connect: {e}") from e

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup connection."""
        if self.connection:
            print("Closing connection")
            self.connection = None
        # Return False to propagate exceptions
        return False

    def query(self, sql: str):
        """Execute query with error handling."""
        if not self.connection:
            raise RuntimeError("Not connected to database")
        # Simulated query
        return {"result": "data"}


# ✅ GOOD: Custom exceptions for better error handling
class DataProcessingError(Exception):
    """Base exception for data processing errors."""

    pass


class InvalidDataError(DataProcessingError):
    """Raised when data format is invalid."""

    pass


class DataTransformationError(DataProcessingError):
    """Raised when data transformation fails."""

    pass


def process_user_data(data: dict) -> dict:
    """
    Process user data with custom exceptions.

    Args:
        data: User data dictionary

    Returns:
        Processed data dictionary

    Raises:
        InvalidDataError: If data format is invalid
        DataTransformationError: If processing fails
    """
    # Validate required fields
    required_fields = ["name", "email", "age"]
    missing_fields = [f for f in required_fields if f not in data]

    if missing_fields:
        raise InvalidDataError(f"Missing required fields: {', '.join(missing_fields)}")

    try:
        # Transform data
        processed = {
            "name": data["name"].strip().title(),
            "email": data["email"].lower(),
            "age": int(data["age"]),
        }

        # Validate age range
        if not 0 <= processed["age"] <= 150:
            raise InvalidDataError(f"Invalid age: {processed['age']}")

        return processed

    except (ValueError, AttributeError) as e:
        raise DataTransformationError(f"Failed to process data: {e}") from e


# ✅ GOOD: Retry logic with exponential backoff
def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
) -> T:
    """
    Retry function with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for each retry

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= backoff_factor
            else:
                print(f"All {max_retries} attempts failed")

    raise last_exception


# Example usage
def main():
    """Demonstrate error handling patterns."""

    # Good file reading
    content = good_file_reader("example.txt")
    if content:
        print(f"File content: {content[:50]}...")

    # Good number checking
    print(f"Is '123' a number? {good_number_checker('123')}")
    print(f"Is 'abc' a number? {good_number_checker('abc')}")

    # Using context manager
    try:
        with DatabaseConnection("postgresql://localhost:5432/db") as db:
            result = db.query("SELECT * FROM users")
            print(f"Query result: {result}")
    except ConnectionError as e:
        print(f"Database error: {e}")

    # Processing data with custom exceptions
    try:
        user_data = {"name": "john doe", "email": "JOHN@EXAMPLE.COM", "age": "30"}
        processed = process_user_data(user_data)
        print(f"Processed user: {processed}")
    except DataProcessingError as e:
        print(f"Data processing error: {e}")

    # Retry logic example
    def unreliable_operation():
        """Simulated unreliable operation."""
        import random

        if random.random() < 0.7:  # 70% failure rate
            raise ConnectionError("Network timeout")
        return "Success!"

    try:
        result = retry_with_backoff(unreliable_operation, max_retries=3)
        print(f"Operation result: {result}")
    except ConnectionError as e:
        print(f"Operation failed after retries: {e}")


if __name__ == "__main__":
    main()
