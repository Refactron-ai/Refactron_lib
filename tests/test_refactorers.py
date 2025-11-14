"""Comprehensive tests for all refactorers."""

from pathlib import Path

from refactron.core.config import RefactronConfig
from refactron.refactorers.add_docstring_refactorer import AddDocstringRefactorer
from refactron.refactorers.extract_method_refactorer import ExtractMethodRefactorer
from refactron.refactorers.magic_number_refactorer import MagicNumberRefactorer
from refactron.refactorers.reduce_parameters_refactorer import ReduceParametersRefactorer
from refactron.refactorers.simplify_conditionals_refactorer import SimplifyConditionalsRefactorer


class TestMagicNumberRefactorer:
    """Test MagicNumberRefactorer functionality."""

    def test_refactorer_name(self):
        config = RefactronConfig()
        refactorer = MagicNumberRefactorer(config)
        assert refactorer.operation_type == "extract_constant"

    def test_extracts_magic_numbers(self):
        config = RefactronConfig()
        refactorer = MagicNumberRefactorer(config)

        code = """
def calculate_discount(price):
    if price > 1000:
        return price * 0.15
    elif price > 500:
        return price * 0.10
    return 0
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0

        # Should suggest extracting constants
        op = operations[0]
        assert "constant" in op.description.lower()
        assert op.risk_score < 0.3  # Should be safe
        assert "THRESHOLD" in op.new_code or "DISCOUNT" in op.new_code

    def test_ignores_common_numbers(self):
        config = RefactronConfig()
        refactorer = MagicNumberRefactorer(config)

        code = """
def process(data):
    result = data * 2  # 2 is common, should be ignored
    if result > 0:
        return result + 1
    return -1
"""

        operations = refactorer.refactor(Path("test.py"), code)
        # Should not suggest extracting 0, 1, 2, -1
        assert len(operations) == 0

    def test_handles_syntax_errors(self):
        config = RefactronConfig()
        refactorer = MagicNumberRefactorer(config)

        code = "def broken function(:"
        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) == 0  # Should handle gracefully


class TestReduceParametersRefactorer:
    """Test ReduceParametersRefactorer functionality."""

    def test_refactorer_name(self):
        config = RefactronConfig()
        refactorer = ReduceParametersRefactorer(config)
        assert refactorer.operation_type == "reduce_parameters"

    def test_detects_too_many_parameters(self):
        config = RefactronConfig(max_parameters=3)
        refactorer = ReduceParametersRefactorer(config)

        code = """
def calculate_total(price, tax, discount, shipping, handling_fee, insurance):
    return price + tax - discount + shipping + handling_fee + insurance
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0

        op = operations[0]
        assert "parameters" in op.description.lower() or "config" in op.description.lower()
        assert op.risk_score > 0.3  # Moderate risk (API change)
        assert "dataclass" in op.new_code or "Config" in op.new_code

    def test_generates_config_class(self):
        config = RefactronConfig(max_parameters=2)
        refactorer = ReduceParametersRefactorer(config)

        code = """
def process(a, b, c, d):
    return a + b + c + d
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0

        op = operations[0]
        # Should generate a config class
        assert "@dataclass" in op.new_code
        assert "Config" in op.new_code
        assert all(param in op.new_code for param in ["a", "b", "c", "d"])

    def test_infers_types(self):
        config = RefactronConfig(max_parameters=2)
        refactorer = ReduceParametersRefactorer(config)

        code = """
def calculate(price, count, is_premium):
    return price * count if is_premium else price
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0

        op = operations[0]
        # Should infer types from names
        assert "float" in op.new_code or "int" in op.new_code

    def test_skips_functions_with_few_parameters(self):
        config = RefactronConfig(max_parameters=5)
        refactorer = ReduceParametersRefactorer(config)

        code = """
def simple(a, b):
    return a + b
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) == 0

    def test_handles_syntax_errors(self):
        config = RefactronConfig()
        refactorer = ReduceParametersRefactorer(config)

        code = "def broken(:"
        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) == 0


class TestAddDocstringRefactorer:
    """Test AddDocstringRefactorer functionality."""

    def test_refactorer_name(self):
        config = RefactronConfig()
        refactorer = AddDocstringRefactorer(config)
        assert refactorer.operation_type == "add_docstring"

    def test_adds_function_docstring(self):
        config = RefactronConfig()
        refactorer = AddDocstringRefactorer(config)

        code = """
def calculate_total(price, tax):
    return price + tax
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0

        op = operations[0]
        assert "docstring" in op.description.lower()
        assert op.risk_score == 0.0  # Perfectly safe
        assert "'''" in op.new_code
        assert "Args:" in op.new_code
        assert "Returns:" in op.new_code

    def test_adds_class_docstring(self):
        config = RefactronConfig()
        refactorer = AddDocstringRefactorer(config)

        code = """
class DataProcessor:
    def process(self):
        pass
"""

        operations = refactorer.refactor(Path("test.py"), code)
        # Should suggest docstring for class
        class_ops = [op for op in operations if "DataProcessor" in op.description]
        assert len(class_ops) > 0

        op = class_ops[0]
        assert "'''" in op.new_code

    def test_skips_private_functions(self):
        config = RefactronConfig()
        refactorer = AddDocstringRefactorer(config)

        code = """
def _private_function():
    return 42
"""

        operations = refactorer.refactor(Path("test.py"), code)
        # Should skip private functions
        assert len(operations) == 0

    def test_skips_functions_with_docstrings(self):
        config = RefactronConfig()
        refactorer = AddDocstringRefactorer(config)

        code = """
def documented_function():
    '''This already has a docstring.'''
    return 42
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) == 0

    def test_generates_appropriate_descriptions(self):
        config = RefactronConfig()
        refactorer = AddDocstringRefactorer(config)

        code = """
def get_user(user_id):
    return None

def set_config(value):
    pass

def is_valid(data):
    return True

def calculate_total(items):
    return sum(items)
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) >= 4

        # Should generate appropriate descriptions based on function names
        descriptions = [op.new_code for op in operations]
        _combined = "\n".join(descriptions)  # noqa: F841

        # Check for contextual descriptions
        assert any("Get" in d or "get" in d for d in descriptions)
        assert any("Set" in d or "set" in d for d in descriptions)
        assert any("Check" in d or "valid" in d for d in descriptions)
        assert any("Calculate" in d or "calculate" in d for d in descriptions)

    def test_handles_syntax_errors(self):
        config = RefactronConfig()
        refactorer = AddDocstringRefactorer(config)

        code = "def broken(:"
        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) == 0


class TestSimplifyConditionalsRefactorer:
    """Test SimplifyConditionalsRefactorer functionality."""

    def test_refactorer_name(self):
        config = RefactronConfig()
        refactorer = SimplifyConditionalsRefactorer(config)
        assert refactorer.operation_type == "simplify_conditionals"

    def test_detects_deep_nesting(self):
        config = RefactronConfig()
        refactorer = SimplifyConditionalsRefactorer(config)

        code = """
def process_order(order_type, amount, customer_type, location):
    if order_type == "online":
        if amount > 100:
            if customer_type == "premium":
                if location == "domestic":
                    return amount * 0.7
                return amount * 0.8
            return amount * 0.9
        return amount
    return amount * 1.05
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0

        op = operations[0]
        assert "nesting" in op.description.lower() or "early return" in op.description.lower()
        assert op.risk_score >= 0.2  # Moderate risk
        assert "guard" in op.reasoning.lower() or "early" in op.reasoning.lower()

    def test_skips_shallow_nesting(self):
        config = RefactronConfig()
        refactorer = SimplifyConditionalsRefactorer(config)

        code = """
def simple_check(x):
    if x > 0:
        return "positive"
    return "negative"
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) == 0  # Shallow nesting is fine

    def test_handles_syntax_errors(self):
        config = RefactronConfig()
        refactorer = SimplifyConditionalsRefactorer(config)

        code = "def broken(:"
        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) == 0


class TestExtractMethodRefactorer:
    """Test ExtractMethodRefactorer functionality."""

    def test_refactorer_name(self):
        config = RefactronConfig()
        refactorer = ExtractMethodRefactorer(config)
        assert refactorer.operation_type == "extract_method"

    def test_detects_long_functions(self):
        """Test that long functions are detected."""
        config = RefactronConfig()
        refactorer = ExtractMethodRefactorer(config)

        # Create a function with >20 statements
        code = """
def very_long_function():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    f = 9
    g = 10
    h = 11
    i = 12
    j = 13
    k = 14
    l = 15
    m = 16
    n = 17
    o = 18
    p = 19
    q = 20
    r = 21
    for item in range(10):
        print(item)
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0
        assert operations[0].operation_type == "extract_method"
        assert (
            "complex block" in operations[0].description.lower()
            or "extract" in operations[0].description.lower()
        )

    def test_suggests_extracting_loops(self):
        """Test that loops in long functions are candidates for extraction."""
        config = RefactronConfig()
        refactorer = ExtractMethodRefactorer(config)

        code = """
def process_data():
    # Many statements to make it long
    x1 = 1
    x2 = 2
    x3 = 3
    x4 = 4
    x5 = 5
    x6 = 6
    x7 = 7
    x8 = 8
    x9 = 9
    x10 = 10
    x11 = 11
    x12 = 12
    x13 = 13
    x14 = 14
    x15 = 15
    x16 = 16
    x17 = 17
    x18 = 18
    x19 = 19
    x20 = 20
    x21 = 21

    # This loop should be suggested for extraction
    for i in range(100):
        result = i * 2
        print(result)
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0
        assert "extract" in operations[0].description.lower()

    def test_risk_score_is_moderate(self):
        """Test that extract method operations have moderate risk."""
        config = RefactronConfig()
        refactorer = ExtractMethodRefactorer(config)

        code = (
            """
def long_function():
    """
            + "\n    ".join([f"x{i} = {i}" for i in range(25)])
            + """
    for i in range(10):
        print(i)
"""
        )

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0

        # Risk should be moderate (0.3-0.7)
        assert 0.3 <= operations[0].risk_score <= 0.7

    def test_skips_short_functions(self):
        """Test that short functions are not flagged."""
        config = RefactronConfig()
        refactorer = ExtractMethodRefactorer(config)

        code = """
def short_function():
    x = 1
    y = 2
    return x + y
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) == 0

    def test_provides_reasoning(self):
        """Test that reasoning is provided for suggestions."""
        config = RefactronConfig()
        refactorer = ExtractMethodRefactorer(config)

        code = (
            """
def long_function():
    """
            + "\n    ".join([f"x{i} = {i}" for i in range(25)])
            + """
    while True:
        break
"""
        )

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0
        assert operations[0].reasoning
        assert len(operations[0].reasoning) > 10

    def test_handles_syntax_errors(self):
        """Test graceful handling of syntax errors."""
        config = RefactronConfig()
        refactorer = ExtractMethodRefactorer(config)

        code = "def broken function(:"
        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) == 0

    def test_handles_with_statements(self):
        """Test detection of with statements."""
        config = RefactronConfig()
        refactorer = ExtractMethodRefactorer(config)

        code = (
            """
def file_processor():
    """
            + "\n    ".join([f"x{i} = {i}" for i in range(25)])
            + """
    with open('file.txt') as f:
        data = f.read()
        process(data)
"""
        )

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0

    def test_only_one_suggestion_per_function(self):
        """Test that only one extraction is suggested per function."""
        config = RefactronConfig()
        refactorer = ExtractMethodRefactorer(config)

        code = (
            """
def long_function():
    """
            + "\n    ".join([f"x{i} = {i}" for i in range(25)])
            + """

    for i in range(10):
        print(i)

    for j in range(10):
        print(j)

    while True:
        break
"""
        )

        operations = refactorer.refactor(Path("test.py"), code)
        # Should only suggest one extraction per function
        assert len(operations) == 1

    def test_code_snippet_extraction(self):
        """Test that code snippets are extracted correctly."""
        config = RefactronConfig()
        refactorer = ExtractMethodRefactorer(config)

        code = (
            """
def long_function():
    """
            + "\n    ".join([f"x{i} = {i}" for i in range(25)])
            + """
    for i in range(10):
        result = i * 2
"""
        )

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0
        assert operations[0].old_code  # Should have old code
        assert operations[0].new_code  # Should have new code

    def test_async_functions_supported(self):
        """Test that async functions are also analyzed."""
        config = RefactronConfig()
        refactorer = ExtractMethodRefactorer(config)

        code = (
            """
async def async_long_function():
    """
            + "\n    ".join([f"x{i} = {i}" for i in range(25)])
            + """
    for i in range(10):
        await process(i)
"""
        )

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0


class TestRefactorerIntegration:
    """Integration tests for refactorers."""

    def test_all_refactorers_work_together(self):
        """Test that all refactorers can run on the same code."""
        config = RefactronConfig()

        refactorers = [
            MagicNumberRefactorer(config),
            ReduceParametersRefactorer(config),
            AddDocstringRefactorer(config),
            SimplifyConditionalsRefactorer(config),
            ExtractMethodRefactorer(config),
        ]

        code = """
def process_data(a, b, c, d, e, f):
    if True:
        if True:
            if True:
                result = a * 100
                return result
    return 0
"""

        all_operations = []
        for refactorer in refactorers:
            operations = refactorer.refactor(Path("test.py"), code)
            all_operations.extend(operations)

        # Should detect multiple types of refactoring opportunities
        assert len(all_operations) > 0

        # Should have different operation types
        operation_types = set(op.operation_type for op in all_operations)
        assert len(operation_types) > 1

    def test_refactorers_provide_complete_information(self):
        """Test that all refactorers provide required information."""
        config = RefactronConfig()
        refactorer = MagicNumberRefactorer(config)

        code = """
def calculate(price):
    if price > 1000:
        return price * 0.15
    return 0
"""

        operations = refactorer.refactor(Path("test.py"), code)
        assert len(operations) > 0

        op = operations[0]
        # Check all required fields
        assert op.operation_type
        assert op.file_path
        assert op.line_number > 0
        assert op.description
        assert op.old_code
        assert op.new_code
        assert 0.0 <= op.risk_score <= 1.0
        assert op.reasoning
