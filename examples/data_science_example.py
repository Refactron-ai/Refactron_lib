"""
Data Science Script Example - Before Refactron

Common issues in data science code that Refactron can detect.
Run: refactron analyze data_science_example.py
"""

import pickle

import pandas as pd
from sklearn.model_selection import train_test_split


# Issue: No docstrings, magic numbers
def load_data(file_path, column1, column2, column3, column4, column5, threshold1, threshold2):
    df = pd.read_csv(file_path)

    # Issue: Magic numbers everywhere
    if len(df) > 1000:
        df = df.sample(500)

    # Issue: Deep nesting
    if df is not None:
        if len(df) > 0:
            if column1 in df.columns:
                if df[column1].notna().sum() > 100:
                    filtered = df[df[column1] > 0]
                    return filtered

    return None


# Issue: Too many parameters
def preprocess_data(
    data,
    remove_nulls,
    normalize,
    scale,
    encode_categorical,
    drop_duplicates,
    fill_strategy,
    scaling_method,
):
    processed = data.copy()

    if remove_nulls:
        processed = processed.dropna()

    if normalize:
        processed = (processed - processed.mean()) / processed.std()

    return processed


# Issue: Hardcoded configuration
def train_model(X, y):
    # Issue: Magic numbers for hyperparameters
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Training code here
    return None


# Issue: Unsafe pickle usage
def save_model(model, filename):
    # Security issue: pickle is unsafe
    with open(filename, "wb") as f:
        pickle.dump(model, f)


def load_model(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)  # Unsafe deserialization


# Issue: No type hints
def calculate_metrics(predictions, actuals):
    accuracy = sum(predictions == actuals) / len(predictions)

    # Issue: Redundant condition
    if True:
        return accuracy


# Issue: Unused function
def unused_analysis():
    pass


# Issue: Dead code after return
def analyze_results(results):
    if results:
        return results.mean()
        print("This will never execute")
        processed_results = results * 2
        return processed_results


# Issue: Complex function that should be split
def do_everything(data, target):
    # Load data
    df = pd.read_csv(data)

    # Clean data
    df = df.dropna()
    df = df.drop_duplicates()

    # Feature engineering
    df["feature1"] = df["col1"] * 2
    df["feature2"] = df["col2"] / 3
    df["feature3"] = df["col3"] ** 2

    # Split data
    X = df.drop(target, axis=1)
    y = df[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

    # Train model
    from sklearn.ensemble import RandomForestClassifier

    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    score = model.score(X_test, y_test)

    # Save
    pickle.dump(model, open("model.pkl", "wb"))

    return score


if __name__ == "__main__":
    # Issue: Hardcoded paths
    data = load_data("data.csv", "col1", "col2", "col3", "col4", "col5", 100, 200)
    result = do_everything("dataset.csv", "target")
    print(f"Accuracy: {result}")
