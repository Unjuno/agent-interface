# Construction outcomes (not pooled with T0 A01)

No formal fixture invocation occurred during construction. These attempts used only the six frozen model definitions and exact local unit checks; they did not call the one-shot `runner.py` or `auditor.py` entrypoints.

| Attempt | Command | Outcome | Disposition |
|---|---|---|---|
| C01 | `python3 -B -m unittest -v test_construction.py` | 8 tests; 5 passed and 3 failed. The independent payload placed `discriminator` at the top level while the candidate nested it under `cases`; a high-interval all-miss assertion expected `1/16`, but the correct four-step product is `1/256`; whole-payload parity consequently failed. | Construction FAIL; no formal source/input allocation used. Contract serialization and the exact path product were corrected without changing the frozen cases or threshold. |
| C02 | `python3 -B -m unittest -v test_construction.py`; `python3 -O -B -m unittest -v test_construction.py`; `python3 -B -m py_compile candidate.py runner.py auditor.py test_construction.py` | 8/8 unit tests passed in normal and optimized modes; compilation exited 0. Candidate DP and independent history enumeration agreed on horizons 1–8 in the preliminary configuration. | Construction PASS for the preliminary horizon set only; formal candidate/auditor invocation counts remain 0/0. After observing high host load, the horizon was prospectively reduced before freeze to 1–4 to reduce CPU work without changing the primary deadline or cases. |
| C03 | `python3 -B -m unittest -v test_construction.py`; `python3 -O -B -m unittest -v test_construction.py`; `python3 -B -m py_compile candidate.py runner.py auditor.py test_construction.py` after prospectively reducing horizons to 1–4. | 8/8 tests passed in normal and optimized modes; compilation exited 0. Candidate DP and independent enumeration agree at every final frozen horizon. | Final construction PASS only; formal candidate/auditor invocation counts remain 0/0. |

The tests establish arithmetic and serialization consistency for authored finite inputs only. They do not establish empirical probability calibration, GUI behavior, or a task-level threshold.
