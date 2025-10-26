"""Test file with intentional issues for manual CLI testing."""

# Unused imports (should be detected)
import os
import sys
import json
import random

# Bad code examples
def bad_function():
    # Magic number
    x = 42
    
    # Boolean comparison
    if x == True:
        # Old-style format
        print("Value is {}".format(x))
    
    # Unused variable
    unused = 100
    
    # Tab character (bad indentation)
	return x

# Missing docstring
def another_function(a, b, c):
    result = a + b + c
    print(result)
    return result

# Trailing whitespace on next line
value = 10   

# More issues
if value == False:
    pass

