"""
Example of well-refactored code that follows best practices.

This demonstrates what code should look like after applying Refactron's suggestions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List

# Constants instead of magic numbers
PREMIUM_DISCOUNT = 0.15
STANDARD_DISCOUNT = 0.10
BASIC_DISCOUNT = 0.05
THRESHOLD_HIGH = 1000
THRESHOLD_MEDIUM = 500
THRESHOLD_LOW = 100


class CustomerType(Enum):
    """Customer types for order processing."""

    PREMIUM = "premium"
    STANDARD = "standard"


@dataclass
class OrderConfig:
    """Configuration for order processing."""

    order_type: str
    amount: float
    customer_type: CustomerType
    location: str
    season: str


def calculate_discount(price: float) -> float:
    """
    Calculate discount based on price thresholds.

    Args:
        price: The original price

    Returns:
        The discount amount
    """
    if price > THRESHOLD_HIGH:
        return price * PREMIUM_DISCOUNT
    elif price > THRESHOLD_MEDIUM:
        return price * STANDARD_DISCOUNT
    elif price > THRESHOLD_LOW:
        return price * BASIC_DISCOUNT
    return 0.0


def calculate_total(price: float, config: OrderConfig) -> float:
    """
    Calculate total order amount.

    Args:
        price: Base price
        config: Order configuration object

    Returns:
        Total amount after all calculations
    """
    # Simple, focused calculation
    discount = calculate_discount(price)
    return price - discount


def filter_positive_values(data: List[int]) -> List[int]:
    """Filter positive values from a list."""
    return [item for item in data if item > 0]


def double_values(data: List[int]) -> List[int]:
    """Double all values in a list."""
    return [item * 2 for item in data]


def filter_by_threshold(data: List[int], threshold: int) -> List[int]:
    """Filter values above a threshold."""
    return [item for item in data if item > threshold]


def process_data(data: List[int]) -> List[int]:
    """
    Process data through multiple transformations.

    This function coordinates several smaller operations,
    making it easy to understand and maintain.

    Args:
        data: Input data list

    Returns:
        Processed data list
    """
    # Each step is clear and testable
    positive_values = filter_positive_values(data)
    doubled = double_values(positive_values)
    filtered = filter_by_threshold(doubled, 10)
    return sorted(filtered)


class DataProcessor:
    """Process and transform data efficiently."""

    def process(self, values: List[int]) -> int:
        """
        Process a list of values.

        Args:
            values: List of integers to process

        Returns:
            Sum of all values
        """
        return sum(values)

    def transform(self, data: List[int]) -> List[int]:
        """
        Transform data with validation.

        Args:
            data: Input data list

        Returns:
            Transformed data or empty list if invalid
        """
        if not self._is_valid_data(data):
            return []

        return [x * 2 for x in data]

    def _is_valid_data(self, data: List[int]) -> bool:
        """
        Validate input data.

        Args:
            data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        if not data:
            return False
        if not isinstance(data, list):
            return False
        if len(data) == 0:
            return False
        if data[0] <= 0:
            return False
        return True


def send_email(recipient: str, subject: str, body: str) -> None:
    """
    Send an email to a recipient.

    Single function instead of multiple duplicate ones.

    Args:
        recipient: Email address of recipient
        subject: Email subject line
        body: Email body content
    """
    print(f"Sending to {recipient}: {subject}")
    print(f"Body: {body}")
