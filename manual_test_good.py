"""Clean test file for comparison."""


def good_function():
    """A well-documented function."""
    value = 42
    
    if value:
        print(f"Value is {value}")
    
    return value


def another_good_function(a: int, b: int, c: int) -> int:
    """
    Add three numbers.
    
    Args:
        a: First number
        b: Second number
        c: Third number
        
    Returns:
        Sum of the three numbers
    """
    result = a + b + c
    return result

