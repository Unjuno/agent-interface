# Independent audit invocation log

The formal allocation itself completed once, in the frozen container. No formal row was rerun or replaced.

## Audit/control attempt 1

The raw-only auditor and copied-evidence controls were launched in separate network-disabled, read-only Docker processes against formal/run01. Both stopped before parsing any row because the runner's output directory did not contain the preregistered SCHEDULE.json required by the auditor. The auditor reported FileNotFoundError for /results/run01/SCHEDULE.json; controls failed on the same missing input when validating its first copied bundle. Neither modified raw.jsonl or summary.json, and neither consumed another formal case.

## Correction and retry boundary

Only the frozen, preformal SCHEDULE.json is copied into this evidence directory. Its SHA-256 must equal the source manifest's 403760a6c89711d86ed42cc0eeda3043d18e6651c5d32ef04d2a5fc70f41a43d. The independent audit and copied-evidence controls may then be invoked against the unchanged first-outcome raw rows. This corrects evidence packaging only; source, schedule, formal rows, and decision gates remain unchanged.

## Audit/control attempt 2

The exact frozen schedule was added and its SHA-256 matched. Against the unchanged raw.jsonl SHA-256 0e39b0d1d29dfc413d842b9a1c2096f812b599d3cc11f301e1131a41ad6ab266, the independent raw-only auditor returned PASS_AUDIT, 18 checks, errors=[] and PASS_X11_STRING8_PY015_BOUNDARY_SCOPED. The copied-evidence controls returned PASS_CONTROLS and rejected all 12/12 corruption probes. This was an audit/bundle correction only; the formal allocation remains one invocation and 30 first-outcome cases.
