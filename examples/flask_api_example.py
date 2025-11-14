"""
Flask API Example - Before Refactron

This is a typical Flask API with common issues that Refactron can detect and fix.
Run: refactron analyze flask_api_example.py
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# Issue: Hardcoded secret
API_KEY = "sk_live_1234567890abcdef"
DATABASE_PASSWORD = "admin123"


# Issue: Too many parameters
@app.route("/calculate")
def calculate_price(base_price, tax_rate, discount, shipping_cost, handling_fee, insurance):
    """Calculate final price with all fees."""
    total = base_price + (base_price * tax_rate) - discount
    total = total + shipping_cost + handling_fee + insurance
    return total


# Issue: Deep nesting and complexity
@app.route("/process_order", methods=["POST"])
def process_order():
    data = request.json

    if data:
        if "user_id" in data:
            if data["user_id"]:
                if "order_type" in data:
                    if data["order_type"] == "premium":
                        if "amount" in data:
                            if data["amount"] > 100:
                                return jsonify({"status": "success", "discount": 0.2})
                            else:
                                return jsonify({"status": "success", "discount": 0.1})
                        else:
                            return jsonify({"error": "Amount missing"}), 400
                    else:
                        return jsonify({"status": "success", "discount": 0})
                else:
                    return jsonify({"error": "Order type missing"}), 400
            else:
                return jsonify({"error": "Invalid user_id"}), 400
        else:
            return jsonify({"error": "User ID missing"}), 400
    else:
        return jsonify({"error": "No data provided"}), 400


# Issue: Using eval - DANGEROUS!
@app.route("/calculate_custom")
def calculate_custom():
    formula = request.args.get("formula")
    result = eval(formula)  # Security vulnerability!
    return jsonify({"result": result})


# Issue: No docstrings
@app.route("/user/<user_id>")
def get_user(user_id):
    # Fetch user from database
    return jsonify({"user_id": user_id})


# Issue: Magic numbers
@app.route("/discount/<int:amount>")
def calculate_discount(amount):
    if amount > 1000:
        return jsonify({"discount": amount * 0.15})
    elif amount > 500:
        return jsonify({"discount": amount * 0.10})
    elif amount > 100:
        return jsonify({"discount": amount * 0.05})
    return jsonify({"discount": 0})


# Issue: Dead code - never called
def unused_helper_function():
    return "This function is never used"


# Issue: Empty function
def process_payment():
    pass


if __name__ == "__main__":
    # Issue: debug=True in production (intentional for demonstration)
    # Security note: This is deliberately insecure for educational purposes
    app.run(debug=True, host="0.0.0.0")  # nosec B104 - example code only
