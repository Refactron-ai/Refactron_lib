"""Module with three safe-to-fix issues.

Issues present:
  - S004: magic number (42, 3.14, 86400)
  - DEP001: unused import (``os``)
  - C002: function too long (>20 lines)
"""

import os  # noqa: F401 — intentionally unused (DEP001 trigger)
from typing import List


def long_data_pipeline(records: List[dict]) -> dict:
    """Process *records* and return a summary.

    This function is intentionally long to trigger C002.
    """
    valid = []
    invalid_count = 0

    for rec in records:
        if "id" not in rec:
            invalid_count += 1
            continue
        if "value" not in rec:
            invalid_count += 1
            continue
        if rec["value"] < 0:
            invalid_count += 1
            continue
        valid.append(rec)

    total = 0.0
    for rec in valid:
        total += rec["value"]

    average = total / len(valid) if valid else 0.0
    threshold = 42  # magic number → S004
    pi_approx = 3.14  # magic number → S004

    above = [r for r in valid if r["value"] > threshold]
    below = [r for r in valid if r["value"] <= threshold]

    seconds_per_day = 86400  # magic number → S004

    # Compute percentile breakdown
    sorted_values = sorted(r["value"] for r in valid)
    n = len(sorted_values)
    if n > 0:
        p25_idx = max(0, n // 4 - 1)
        p50_idx = max(0, n // 2 - 1)
        p75_idx = max(0, 3 * n // 4 - 1)
        p25 = sorted_values[p25_idx]
        p50 = sorted_values[p50_idx]
        p75 = sorted_values[p75_idx]
    else:
        p25 = 0
        p50 = 0
        p75 = 0

    # Compute variance
    variance = 0.0
    for rec in valid:
        diff = rec["value"] - average
        variance += diff * diff
    variance = variance / n if n > 0 else 0.0

    return {
        "total": total,
        "average": average,
        "variance": variance,
        "p25": p25,
        "p50": p50,
        "p75": p75,
        "above_threshold": len(above),
        "below_threshold": len(below),
        "invalid": invalid_count,
        "pi": pi_approx,
        "seconds_per_day": seconds_per_day,
    }
