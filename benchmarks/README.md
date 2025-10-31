# Benchmarks

This directory contains performance benchmarking scripts for Refactron.

## Running Benchmarks

```bash
# Run performance benchmark
python benchmarks/performance_benchmark.py
```

## Benchmark Scripts

### performance_benchmark.py

Measures the performance of core Refactron operations:
- Analysis time for different file sizes (small, medium, large)
- Refactoring suggestion generation time
- Statistical analysis (mean, median, std dev, min, max)

### Example Output

```
🚀 Starting Refactron Performance Benchmarks...

Benchmarking with small file...
Benchmarking with medium file...
Benchmarking with large file...

================================================================================
REFACTRON PERFORMANCE BENCHMARK RESULTS
================================================================================

Operation: analyze_small
  Mean time:   0.1234s
  Median time: 0.1200s
  Min time:    0.1150s
  Max time:    0.1350s
  Std dev:     0.0082s
  Iterations:  5
...
```

## Adding New Benchmarks

To add a new benchmark:

1. Create a new function following the pattern:
```python
def benchmark_operation(name: str, operation, iterations: int = 5):
    # Benchmark logic
    pass
```

2. Add it to the main() function
3. Document it in this README

## Performance Goals

Current performance targets:
- Small file (100 lines): < 0.2s
- Medium file (500 lines): < 1.0s
- Large file (2000 lines): < 5.0s

## Continuous Monitoring

We track performance over time to:
- Identify performance regressions
- Validate optimization efforts
- Set realistic expectations for users
