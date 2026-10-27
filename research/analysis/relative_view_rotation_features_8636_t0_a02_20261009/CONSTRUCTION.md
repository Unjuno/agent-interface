# Construction and verification

Before the source freeze, `python -m unittest -v test_construction.py` and `python -O -m unittest -v test_construction.py` each passed 11/11 tests. The added regression reuses the A01 seed-30011 focal-shift shape-gate case only to validate the corrected decision taxonomy; it is not part of A02's formal seed set.

No candidate or independent-auditor CLI command is part of the construction suite. After the formal HOLD, do not rerun either formal command. Package integrity and repository indexes are validated separately.
