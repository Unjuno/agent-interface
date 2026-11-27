# Construction checks

These construction checks are separate from the frozen one-shot candidate and raw-only auditor invocations.

- Command: `python3 -B test_construction.py`
- Exit: 0
- Output: `construction-normal.stdout.txt` and `construction-normal.stderr.txt`
- Command: `python3 -B -O test_construction.py`
- Exit: 0
- Output: `construction-optimized.stdout.txt` and `construction-optimized.stderr.txt`
