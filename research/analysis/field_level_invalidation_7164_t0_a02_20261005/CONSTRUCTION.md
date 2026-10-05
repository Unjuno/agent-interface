# A02 construction receipt

The A01 formal output exposed a gate-classification bug: expected stale-value
counterexamples from the deliberately weak `independent_field` comparator were
included in the blocking audit error list. A02 preserves A01 unchanged and
changes only the independent auditor's classification: derived-field mismatches
from that comparator become expected negative-control evidence, while receipt,
identity, and recomputation-count errors remain blocking.

Before A02 freeze, on macOS arm64 / CPython 3.14.5, the following construction
checks passed:

- `python3 construction_tests.py` → `CONSTRUCTION_TESTS_PASS`
- `python3 -m py_compile candidate.py audit.py construction_tests.py` → exit 0
- `python3 -m json.tool INPUT.json` and `SCHEMA.json` → exit 0
- `git diff --check` → exit 0

These are construction checks, not formal candidate/auditor outputs. A02 gets a
new freeze ID and a distinct empty `formal_02/` output directory. Candidate and
auditor each remain limited to one sequential container invocation.
