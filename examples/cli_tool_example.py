"""
CLI Tool Example - Before Refactron

Common issues in CLI applications that Refactron can detect.
Run: refactron analyze cli_tool_example.py
Run: refactron refactor cli_tool_example.py --preview
"""

import argparse
import os
import sys

# Issue: Hardcoded configuration
API_ENDPOINT = "https://api.example.com"
API_TOKEN = "secret_token_12345"
MAX_RETRIES = 5


# Issue: No docstrings, too many parameters
def process_file(
    input_path, output_path, format_type, compression, encoding, backup, overwrite, verbose, dry_run
):

    # Issue: Deep nesting
    if os.path.exists(input_path):
        if os.path.isfile(input_path):
            if os.access(input_path, os.R_OK):
                with open(input_path, "r") as f:
                    data = f.read()

                    if data:
                        if len(data) > 0:
                            if format_type == "json":
                                if not dry_run:
                                    processed = data.upper()
                                    if overwrite:
                                        with open(output_path, "w") as out:
                                            out.write(processed)
                                    return processed
    return None


# Issue: Magic numbers
def calculate_size(file_path):
    size = os.path.getsize(file_path)

    if size > 1048576:  # 1MB in bytes
        return f"{size / 1048576:.2f} MB"
    elif size > 1024:  # 1KB in bytes
        return f"{size / 1024:.2f} KB"
    return f"{size} bytes"


# Issue: Using eval - dangerous!
def evaluate_expression(expr):
    result = eval(expr)
    return result


# Issue: Shell injection vulnerability
def run_command(user_input):
    command = f"ls {user_input}"
    os.system(command)  # Unsafe!


# Issue: No type hints
def validate_config(config):
    if config:
        if "api_key" in config:
            if len(config["api_key"]) > 10:
                return True
    return False


# Issue: Dead code
def unused_helper():
    return "Never called"


def another_unused_function():
    pass


# Issue: Empty function
def setup_logging():
    pass


# Issue: Redundant condition
def check_status(status):
    if True:
        if status == "active":
            return True
    return False


# Issue: Complex main function that needs refactoring
def main():
    parser = argparse.ArgumentParser(description="Process files")
    parser.add_argument("input", help="Input file")
    parser.add_argument("output", help="Output file")
    parser.add_argument("--format", default="text")
    parser.add_argument("--compress", action="store_true")
    parser.add_argument("--encoding", default="utf-8")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    # Issue: Too many parameters
    result = process_file(
        args.input,
        args.output,
        args.format,
        args.compress,
        args.encoding,
        args.backup,
        args.overwrite,
        args.verbose,
        args.dry_run,
    )

    # Issue: Magic number
    if result and len(result) > 10000:
        print("Large output")

    # Issue: Hardcoded timeout
    import time

    time.sleep(5)

    # Issue: Using system() with user input
    if args.verbose:
        os.system(f"echo Processing {args.input}")  # Shell injection!

    return 0


# Issue: No docstring
def cleanup_temp_files(directory):
    for file in os.listdir(directory):
        if file.endswith(".tmp"):
            os.remove(os.path.join(directory, file))


# Issue: Unreachable code
def process_data(data):
    if data is None:
        return None

    return data.strip()

    # Dead code below
    processed = data.lower()
    validated = processed.strip()
    return validated


if __name__ == "__main__":
    sys.exit(main())
