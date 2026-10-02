# Pre-freeze construction record

- Initial construction suite: 5 tests, 3 errors. The independent perfect-duplicate check has zero-probability outcomes; both candidate and auditor initially attempted to normalize those impossible hypothetical histories.
- Repair: exclude zero-probability outcomes only from expectation sums/tree expansion; preserve them in the declared likelihood table. No probability, prior, cost, utility, gate, or decision threshold was changed.
- Revised construction suite: `python -B -m unittest -v test_contract.py` — 5/5 PASS.
- `python -m py_compile candidate.py audit.py test_contract.py` — exit 0.
- `git diff --check` — no output / exit 0.
- No candidate or auditor CLI/full computation ran during construction. Formal execution budget remains candidate=0, independent auditor=0, retries=0.
- Docker Desktop service cannot be opened by this user process; a current Issue #6176 resource note also records an unrelated running shared OrbStack container and no available exclusive slot. No container/service was inspected, entered, started, stopped, or modified.
