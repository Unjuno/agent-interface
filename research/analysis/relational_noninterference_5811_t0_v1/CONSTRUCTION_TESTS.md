# Construction checks — Issue #5811 T0

Status: **CONSTRUCTION PASS / NOT FROZEN**. The current local construction suite passes. Formal Docker candidate and independent-auditor allocations have not started; there is no formal result and no production or live-isolation claim.

Construction command:

```powershell
python -B -m unittest research.analysis.relational_noninterference_5811_t0_v1.test_t0 -v
```

Latest run on Python 3.12 (local Windows): 8 tests, 8 passed. Earlier construction runs exposed inconsistent meanings for coverage counts, a malformed fixture serialization during a PowerShell repair attempt, and a nested-vs-scalar generation comparison bug in the independent auditor. These construction failures were corrected before any formal allocation and are not experiment data.

The fixture has ten named cases. Only the clean disjoint and two fully audited contamination cases support scoped relation claims; incomplete dependency evidence remains UNKNOWN. The capacity-only shared queue is independently inventoried and its allowed queue-use rows are omitted only from semantic projection equality, not from dependency auditing. This result only permits proceeding to freeze review; it is not the formal result.
