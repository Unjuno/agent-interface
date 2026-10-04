# #6695 reversible preparation deadline frontier A01

Finite synthetic construction/method evidence. See [PROTOCOL.md](PROTOCOL.md), [CONSTRUCTION_HISTORY.md](CONSTRUCTION_HISTORY.md), and, after execution, REPORT.md. Prior #6695 T0 remains immutable. Runtime candidate/auditor counters are recorded in EXECUTION.json after execution.

Reproduce construction: `python -B -m unittest discover -s . -p 'test_*.py' -v`. Use `candidate.py fixtures.json NEW_RAW.jsonl` and then `auditor.py fixtures.json truth.json NEW_RAW.jsonl NEW_AUDIT.json` only for a separately authorized ordinary reproduction; do not overwrite or regrade this allocation. Candidate must have no truth-file access; original commands/limits are preserved in EXECUTION.json.
