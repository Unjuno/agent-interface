# R07 result — TASK AND GENERATION GATES PASS; CLEANUP ASSERTION FAIL

## Functional outcomes

The normal-mode positive case returned `TASK_SUCCEEDED`. The loopback scorer
recorded exactly one POST, `value=t9910254`, with `exact: true`, and the outer
score matched. Both actions were admitted and completed. This is a first
fixture-level success of the composed Edge V5 → caller v3 → compiled GUI path.

The changed-generation case returned `EXECUTION_INCOMPLETE` with
`association_changed`, one completed action, and no POST or outer score. The
actual compiled handle-store admission was `SCOPE_MISMATCH` with reason
`window_generation_changed_or_missing`, and no submit dispatch occurred.

## Run status and cleanup

The unittest command exited 1 because the runner's profile cleanup helper
could not remove Edge child-process locks. Thus R07 is **not a clean test-suite
pass** and did not run the `-O` mode. The functional results above are
preserved as individual case outcomes, not promoted to a complete R07 pass.

Only Edge processes whose command line contained each generated R07 profile
marker were stopped. Follow-up checks found zero matching processes and both
temporary profile directories absent. The task verdicts are unchanged. See
[`raw/cleanup-audit.json`](raw/cleanup-audit.json).

## Evidence and boundary

- Frozen protocol: [`PROTOCOL.md`](PROTOCOL.md).
- Normal-mode conditions and source hashes: [`raw/normal/conditions.json`](raw/normal/conditions.json).
- Both individual case records, screenshots, OCR, admissions, POSTs and receipts: [`raw/normal/`](raw/normal/).
- Runner stdout/exit: [`raw/normal.stdout.txt`](raw/normal.stdout.txt), [`raw/normal.exit.txt`](raw/normal.exit.txt).

This headless Edge/CDP fixture does not establish physical input release,
provider cost, repeated reliability, Calc/MAP01 coverage, matched efficiency,
or public runtime readiness.
