# A04 retained candidate trace — posthoc audit A05

## Purpose and boundary

This is a new, read-only reconstruction of the retained A04 candidate trace. It
uses only bytes copied from the pre-run A04 source commit and the later commit
that archived A04's formal raw/logs. It does not invoke A04's candidate, its
formal auditor, a container, X11, a game, a model, or any input path.

A04 remains `STOP / consumed`: its single formal auditor invocation exited 1
before reconstruction. A05 cannot replace that failed invocation, change the
formal allocation disposition, or assign a scientific result. The only
possible positive result is that this posthoc program independently rebuilds
what the retained candidate JSON says.

## Question

Does the archived `RESULT.json`, taken byte-for-byte, contain two distinct
same-owner admissions for `A` followed by one explicitly reported ambiguous
release, while preserving the logged fake-Xlib call sequence, nested owner
receipt timing, false authority flags, and neutral fake keymap?

The audit separately checks custody. It expects the A04 manifest's three
`current_main_blobs` values to disagree with the actual Git objects at its
declared main commit, and expects `prefreeze-audit-attempts.log` to be absent
from the frozen source tree. Those are preserved provenance/manifest defects,
not patched or silently normalized.

## Reproduction

From this directory, run:

```powershell
python -B audit_readonly.py
python -B -m unittest -v test_posthoc_audit.py
```

The auditor reads `inputs/` without modifying it and writes only
`AUDIT.json` beside itself. The test suite uses temporary copies for corruption
checks. Compare each input file with `A05_FREEZE.json` before interpreting the
report.

## Scope

Even a successful reconstruction only describes the saved fake-Xlib candidate
record. It says nothing about real X11/server delivery, physical release,
application consumption, MAP01, task effect, threat response, feedback,
recovery, safety, latency, or authority. No live #59 allocation is implied.
