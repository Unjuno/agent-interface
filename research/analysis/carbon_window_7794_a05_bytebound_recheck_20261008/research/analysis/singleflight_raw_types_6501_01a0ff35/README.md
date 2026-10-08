# #6501 supplemental raw-type boundary

Read [REPORT.md](REPORT.md) for the observed defect, scoped repair and limits;
[PROTOCOL.md](PROTOCOL.md) records the prospective finite check.
Original T0/T0b artifacts remain unchanged.

Reproduce the regression without changing any result file:

```powershell
python -B -m unittest discover -s research/analysis/singleflight_raw_types_6501_01a0ff35 -p 'test_*.py' -v
```

To reproduce the supplemental matrix, copy `characterize.py`, `check_matrix.py`,
`legacy_auditor.py`, `auditor_v2.py`, `fixtures.json` and `retained-raw.json`
byte-for-byte into a fresh scratch directory. Run `python characterize.py`
and then `python check_matrix.py` there. Both create results exclusively and
refuse to overwrite an existing matrix/audit. This is a repeatable construction
check, not permission to rerun the original formal scheduler allocations.

`SHA256SUMS` covers this retained package except itself. `provenance.json`
records the original Git blob identities; `validation.json` records additional
local checks with their actual exit codes. Historical tests and matrix raw are
retained separately.
