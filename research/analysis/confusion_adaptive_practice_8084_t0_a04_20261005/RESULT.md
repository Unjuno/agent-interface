# A04 retained outcome — `HOLD_METHOD_GATE`

## Executed outcome

- Fixture generator: exit 0; 6,000 rows across four authored strata × three sample sizes × 500 replicates.
- Candidate: one WSLc call, exit 0; 6,000 output rows; raw stdout 449,080 bytes. Candidate mount exposed only `candidate.py` and the observed-count fixture.
- Auditor launcher: first WSLc launch returned `ERROR_DISK_FULL` before Python started; preserved separately as `auditor-launch-attempt1.*`. After minimal-container and read-only-mount diagnostics passed, the auditor process was invoked once, exit 0, with separate auditor-only scorer truth.
- Independent reconstruction: 6,000 base rows; no base reconstruction errors. Four mutation controls rejected. The duplicate-row mutation **survived**, because the auditor collapsed raw rows to a dictionary before checking cardinality. This violates the frozen method gate; A04 therefore remains `HOLD_METHOD_GATE` and is not promoted to an accepted result.

## Descriptive screen from the retained auditor output (not accepted as a method pass)

The unchanged A02 span/peak rule crossed the frozen diagnostic-screen limits on the authored data: at n=20, low-dispersion false activation was 169/500 (0.338; limit 0.05), despite uniform-control false activation 11/500 (0.022). At n=100, low-dispersion false activation was 21/500 (0.042), uniform 0/500. Strong/margin activation and top-pair accuracy met their n≥20 thresholds in this one deterministic seed family. These are machine-produced descriptive counts, but because the duplicate-row mutation survived, they are retained as provisional, not an accepted method result or calibration claim.

## Preserved failures / scope

A03's separate `STOP_AUDIT_INPUT_HANDOFF_PATH_ERROR` remains untouched. A04's preformal redirection/allowlist mistakes, first auditor-launch infrastructure error, all stdout/stderr, and the duplicate-row mutant are preserved. No candidate or auditor was rerun. The next fresh allocation corrects the row-cardinality audit and uses a disjoint seed family. No participants, GUI, learning, retention, transfer, safety, or runtime effect was tested.
