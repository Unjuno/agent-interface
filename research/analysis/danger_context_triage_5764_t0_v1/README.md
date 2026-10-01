# Danger-context optional-audit triage — Issue #5764 T0

This package retains one frozen, deterministic CPU experiment over an authored 12-event stream. It evaluates optional post-event audit selection only; it is not a runtime authority or alert-suppression policy.

## Result

The candidate ran once and emitted six selectors under the same optional budget of four. The original independent auditor invocation is preserved as `STOP_AUDITOR_FREEZE_SCHEMA_ADAPTER`; it was not retried. A separately preregistered read-only v2 adapter audited the unchanged candidate raw once and passed all six selector replays, full-denominator checks, mandatory-lane preservation, and six corruption controls.

The dual selector found 3/5 optional synthetic failures, matching EFFECT_ONLY (3/5), versus 2/5 for the #5435 SAFE_IDENTITY_BATCH fixed-budget adapter, 0/5 for NOVELTY_ONLY and #5435 SEVERITY_ONLY, and 1/5 chronological. Thus this fixture demonstrates no incremental discovery from adding novelty to the linked effect signal. These hand-authored counts do not support real-world comparative yield, risk, or safety claims.

## Files

- `FREEZE.json` and `AUDIT_V2_FREEZE.json`: pre-execution identities and gates.
- `preaudit_stream.json`: selector-visible events, with no outcome labels.
- `sealed_outcomes.json`: separate synthetic scorer labels, used only after selection.
- `run.py` / `runner.py`: frozen candidate and deterministic selectors.
- `audit.py`: initial independent raw-only auditor; its first invocation STOP is retained in `AUDIT_V1_STOP.md`.
- `audit_v2.py`: schema adapter that calls the unchanged independent v1 replay core; it does not import the candidate.
- `results/raw.json` and `results/audit_v2.json`: immutable first candidate and corrected audit outputs.
- `test_*.py`: local construction and adapter tests; tests are not a new formal allocation.

See `REPORT.md` for H/T/D/C/U and full scope; `EXECUTION.md` preserves commands, exits, environment, and the two distinct audit versions.
