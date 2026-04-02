"""Module where removing an import would break runtime behaviour.

``collections`` is used three lines below its import via
``collections.OrderedDict``, but a naive unused-import fixer that only
checks for bare ``Name`` nodes might miss the dotted attribute access
and try to remove it.

``sys`` is genuinely unused and safe to remove (DEP001 trigger).
"""

import collections
import sys  # intentionally unused — safe to remove (DEP001)  # noqa: F401


def ordered_merge(mapping_a, mapping_b):
    merged = collections.OrderedDict()
    for key, value in mapping_a.items():
        merged[key] = value
    for key, value in mapping_b.items():
        if key not in merged:
            merged[key] = value
    return merged
