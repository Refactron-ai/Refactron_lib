"""
Example of code with various issues that Refactron can detect.

This file intentionally contains code smells, complexity issues,
and other problems for demonstration purposes.
"""


# Issue: Too many parameters
def calculate_total(price, tax, discount, shipping, handling_fee, insurance):
    result = price + tax - discount + shipping + handling_fee + insurance
    return result


# Issue: High complexity and deep nesting
def process_order(order_type, amount, customer_type, location, season):
    if order_type == "online":
        if amount > 100:
            if customer_type == "premium":
                if location == "domestic":
                    if season == "holiday":
                        return amount * 0.7
                    else:
                        return amount * 0.8
                else:
                    return amount * 0.85
            else:
                return amount * 0.9
        else:
            return amount
    else:
        return amount * 1.05


# Issue: Magic numbers
def calculate_discount(price):
    if price > 1000:
        return price * 0.15
    elif price > 500:
        return price * 0.10
    elif price > 100:
        return price * 0.05
    return 0


# Issue: No docstring
def mystery_function(x, y):
    z = x * 42 + y * 3.14159
    return z


# Issue: Very long function
def do_everything(data):
    result = []
    for item in data:
        if item > 0:
            temp = item * 2
            result.append(temp)

    filtered = []
    for item in result:
        if item > 10:
            filtered.append(item)

    sorted_data = sorted(filtered)

    final = []
    for item in sorted_data:
        if item % 2 == 0:
            final.append(item * 3)
        else:
            final.append(item * 2)

    return final


class DataProcessor:
    def process(self, a, b, c, d, e, f):
        return a + b + c + d + e + f

    def transform(self, data):
        if data:
            if isinstance(data, list):
                if len(data) > 0:
                    if data[0] > 0:
                        return [x * 2 for x in data]
        return data


# Duplicate-looking functions
def send_email1(recipient, subject, body):
    print(f"Sending to {recipient}: {subject}")


def send_email2(recipient, subject, body):
    print(f"Sending to {recipient}: {subject}")


def send_email3(recipient, subject, body):
    print(f"Sending to {recipient}: {subject}")
