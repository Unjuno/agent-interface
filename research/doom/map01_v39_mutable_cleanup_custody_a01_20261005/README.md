# Mutable cleanup record custody probe

This additive synthetic experiment tests whether the bridge's cursor-based drain
observes an `owner_release` record's final fields when the owner appends the
record before aggregate reconciliation and mutates that same dictionary after
reconciliation.

Run 01 freezes the PR #7829 candidate and its harness inputs under `SOURCE/`,
uses a deterministic append → drain → mutation barrier, and retains the exact
container log, exit status, source hashes, base SHA, and candidate SHA under
`results/run01/`. The probe reproduced stale bridge state after the owner record
became verified neutral. This is a component-level synthetic result only; it
makes no claim about live-display frequency or application effect.

Command and pinned environment are recorded in `results/run01/RESULT.json`.
