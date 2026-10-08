# Setup and audit attempts

Two pre-measurement setup failures and one initial auditor setup failure are preserved to distinguish them from the single measured candidate run:

1. A04 candidate preflight exited before frame loading because the copied runner expected `audit_a03.py`; only `audit_a04.py` was present. Snapshot: `attempts/FREEZE_A04_preflight01.json`.
2. A04b candidate preflight returned `HOLD_PREDECESSOR_HASH`: PowerShell text redirection had altered the bytes of the copied A02 predecessor JSON. Snapshot: `attempts/FREEZE_A04b_preflight02.json`.
3. A04c setup retrieved those two predecessor blobs through binary `git show` output and checked their SHA-256 values before the sole candidate measurement.
4. The first post-run audit stopped before row reconstruction because it expected the frozen candidate under `analyze_a03.py`. A byte-identical alias was added; the corrected independent audit completed once and passed 5/5 mutation controls. Candidate results were not rerun.

The aliases `analyze_a03.py` / `audit_a03.py` are byte-identical copies required by inherited A03 path checks; the executed A04 files remain `analyze_a04.py` and `audit_a04.py`.
