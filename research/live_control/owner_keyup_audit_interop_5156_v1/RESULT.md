# Allocation 05 result

## Outcome

`PASS_JOIN_CONSTRUCTION_SYNTHETIC_ONLY` — the adapter reconciled three frozen
owner-v1-shaped rows with two explicit caller-v3 receipts and one independently
listed cleanup release. The same key was released explicitly twice; the frozen
sequence and non-overlapping caller intervals assigned distinct release IDs.
The cleanup row remained autonomous and received no fabricated caller interval.
The resulting three v2 rows passed the unchanged PR #5415 completeness
auditor (`errors=[]`).

This composes the two audit contracts for a synthetic fixture only. It does not
repair, merge, or promote PR #5298 or #5415, and it does not show that a live
owner run emits a complete independently bound inventory.

## Commands and evidence

- Frozen suite: `python -B -m unittest -v test_join.py` — 14 tests passed.
- Syntax check: in-memory `compile()` of the five Python sources — PASS.
- Runner, exactly once: `python -B run_join.py` — 3 rows, raw SHA-256
  `56842934B9F9B13FE0E52D515D31BD0C3D598CDB1CFA8B719DFB4C8BA463CBC2`.
- Separate completeness audit, exactly once after runner exit 0:
  `python -B audit_join.py` — PASS, zero errors, same raw hash.
- Runner and auditor verify pinned source hashes before operating. Full inputs,
  run receipt, audit receipt, and checksums are retained in this directory.

The initial frozen tests produced RED: 13 tests errored because the join was
unimplemented; after implementation all 14 passed. Rejection controls exercise
empty/all-omitted rows, one-row omission, duplicate/wrong-identity rows,
missing/duplicate/overlapping caller receipts, inverted owner/caller intervals,
duplicate expected sequence, authority/physical claims, and unexpected rows.
Direct v1 rows—including rows augmented only with caller timestamps—still fail
the v2 auditor for schema/release-ID/inventory reasons. The adapter is the
explicitly tested boundary between the contracts.

## Scope / stop reason

This is synthetic construction on CPython 3.12.10 / Windows host. No Docker or
OrbStack command was invoked because #5085 still requires a fresh exact named
shared-resource allocation; no X11, GUI/input, MAP01, model, or GPU was used.
No live physical state or application effect is established. Keep formal X11,
held-input occupancy, independent first useful feedback, matched recovery
coverage, and cross-domain transfer open. The v2 auditor itself does not check
caller nesting; that property is checked by this construction adapter's
mutation suite, not by the independent completeness audit.
