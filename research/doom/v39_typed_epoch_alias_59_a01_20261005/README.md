# V39 typed epoch alias A01

This is a small current-main source-boundary construction experiment for Issue #59. It asks whether the typed health/ammo snapshot boundary rejects Boolean and float metadata that compares equal to the enclosing integer observation epoch.

## H / T / D / C / U

See [PREREGISTRATION.md](PREREGISTRATION.md). The exact source commit, blobs and hashes are pinned in [SOURCE_MAP.json](SOURCE_MAP.json); `FREEZE.json` binds the source, fixture, preregistration, runner, auditor and exact commands before execution.

## Scope

The source pipeline accepted the exact-integer control and all eight malformed aliases. The raw-only auditor independently reconstructs every row and the resulting fail-open classification. This is an offline boundary-contract result only: it does not show that the in-tree readers emit malformed values or that an action received input authority. No source code, live game, model, GUI, OS input, shared resource or live allocation was used.

This result supports exact-type validation at the typed snapshot boundary as a candidate repair. It does not complete the Issue #59 live threat-control, per-key release, independently useful feedback, recovery or separately labelled MAP01 gates.

The candidate's original classification label was incorrect (`FAIL_CLOSED` despite accepting malformed rows). The raw freeze and result are retained unchanged; see [the separate interpretation correction](CORRECTION.md), which classifies the observed source behavior as fail-open.

## Reproduction

Run `python -B run_probe.py` once, then `python -B audit.py` once. The first command produces `RESULT.json`; the second writes `AUDIT.json`. Commands, captured stdout/stderr, exit codes and a checksum manifest are retained alongside the result.
