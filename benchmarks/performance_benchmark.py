#!/usr/bin/env python3
"""
Performance benchmarking script for Refactron.

This script measures the performance of various Refactron operations
to help identify bottlenecks and track performance over time.
"""

import time
from pathlib import Path
import tempfile
import statistics
from typing import List, Dict, Any

from refactron import Refactron
from refactron.core.config import RefactronConfig


def create_test_file(size: str = "small") -> Path:
    """Create a test Python file of specified size."""
    sizes = {
        "small": 100,  # 100 lines
        "medium": 500,  # 500 lines
        "large": 2000,  # 2000 lines
    }

    lines = sizes.get(size, 100)

    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)

    # Generate code
    temp_file.write("# Auto-generated test file\n")
    temp_file.write("import os\nimport sys\n\n")

    for i in range(lines // 10):
        temp_file.write(
            f"""
def function_{i}(param1, param2, param3):
    '''Docstring for function_{i}.'''
    result = 0
    for j in range(10):
        if j % 2 == 0:
            result += j * param1
        else:
            result -= j * param2
    return result + param3

"""
        )

    temp_file.close()
    return Path(temp_file.name)


def benchmark_operation(name: str, operation, iterations: int = 5) -> Dict[str, Any]:
    """Benchmark an operation multiple times and return statistics."""
    times = []

    for _ in range(iterations):
        start = time.time()
        operation()
        end = time.time()
        times.append(end - start)

    return {
        "name": name,
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "min": min(times),
        "max": max(times),
        "iterations": iterations,
    }


def benchmark_analysis(refactron: Refactron, file_path: Path) -> Dict[str, Any]:
    """Benchmark the analysis operation."""
    return benchmark_operation("analyze", lambda: refactron.analyze(file_path))


def benchmark_refactoring(refactron: Refactron, file_path: Path) -> Dict[str, Any]:
    """Benchmark the refactoring operation."""
    return benchmark_operation("refactor", lambda: refactron.refactor(file_path, preview=True))


def print_results(results: List[Dict[str, Any]]) -> None:
    """Print benchmark results in a formatted table."""
    print("\n" + "=" * 80)
    print("REFACTRON PERFORMANCE BENCHMARK RESULTS")
    print("=" * 80 + "\n")

    for result in results:
        print(f"Operation: {result['name']}")
        print(f"  Mean time:   {result['mean']:.4f}s")
        print(f"  Median time: {result['median']:.4f}s")
        print(f"  Min time:    {result['min']:.4f}s")
        print(f"  Max time:    {result['max']:.4f}s")
        print(f"  Std dev:     {result['stdev']:.4f}s")
        print(f"  Iterations:  {result['iterations']}")
        print()


def main():
    """Run the benchmark suite."""
    print("🚀 Starting Refactron Performance Benchmarks...\n")

    # Initialize Refactron
    config = RefactronConfig.default()
    refactron = Refactron(config)

    results = []

    # Test different file sizes
    for size in ["small", "medium", "large"]:
        print(f"Benchmarking with {size} file...")
        test_file = create_test_file(size)

        try:
            # Benchmark analysis
            result = benchmark_analysis(refactron, test_file)
            result["name"] = f"analyze_{size}"
            results.append(result)

            # Benchmark refactoring
            result = benchmark_refactoring(refactron, test_file)
            result["name"] = f"refactor_{size}"
            results.append(result)

        finally:
            # Clean up
            test_file.unlink()

    # Print results
    print_results(results)

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTotal operations benchmarked: {len(results)}")

    analyze_times = [r["mean"] for r in results if "analyze" in r["name"]]
    if analyze_times:
        print(f"Average analysis time: {statistics.mean(analyze_times):.4f}s")

    refactor_times = [r["mean"] for r in results if "refactor" in r["name"]]
    if refactor_times:
        print(f"Average refactoring time: {statistics.mean(refactor_times):.4f}s")

    print("\n✅ Benchmarking complete!")


if __name__ == "__main__":
    main()
