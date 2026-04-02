"""Module whose public function is tested by fixture_test_break_test.py.

If autofix changes the function signature (e.g. extracts ``tax_rate``
into a module-level constant and removes the parameter), the
companion test file will break.  The Verification Engine's
TestSuiteGate must block such transforms.

Issues present:
  - S004: magic number ``100`` inside the function body
  - DEP001: unused import ``math``
"""

import math  # intentionally unused — DEP001 trigger  # noqa: F401


def calculate_total(items, tax_rate=0.1):
    subtotal = sum(items)
    if subtotal > 100:  # S004 — magic number
        discount = subtotal * 0.05
        subtotal -= discount
    return round(subtotal * (1 + tax_rate), 2)
