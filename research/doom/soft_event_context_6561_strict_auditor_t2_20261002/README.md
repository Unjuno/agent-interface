# Issue #6561 — strict soft-event receipt auditor T2

This is a fresh host-CPU-only successor to T1, not a retry of its candidate or auditor and not the WSLc allocation in #6561. It preserves all T1 bytes. T1's retained outcomes show the old target auditor accepted the valid control and all four declared corruptions; its separate postrun auditor was not retained (`STOP_POSTRUN_AUDIT_NOT_RETAINED`).

## H — Hypothesis

A new raw-only auditor, anchored to an out-of-band expected binding and the complete frozen `SOFT_CHANGED` contract, accepts a complete control and rejects common-mode rebinding, each of three contradictory authority/decision fields, and omission of required guard fields.

## T — Frozen test

At main `86648743927be33053a3516ad9fb9e0aaefd6425`, use only the immutable T1 packet bytes. Create a new control fixture that adds the two `SOFT_CHANGED` booleans omitted from T1's fixture (`may_only_preserve_or_reduce_existing_authority=true`, `semantic_change_identified=true`), matching the frozen guard implementation. Generate five preregistered mutations. Run the six packet classifications once in-process; if and only if the candidate exits zero, run the separate `audit_t2.py` once against the retained raw packets and receipt. The independent auditor checks source/input hashes, old T1 false-acceptance record, exact mutation/rejection reason families, and host-only scope without importing the candidate or target auditor.

Construction tests (`python -B -m unittest -v test_t2.py`) are preparation only. Formal candidate output is uniquely `results/t2-20261002-01`; both candidate and auditor refuse a missing/existing output respectively. No retry or substitute data.

## D — Decision

Scoped PASS only if the complete control is accepted, all five mutations are rejected for their declared reason families, T1's five retained subprocess outcomes still show four accepted corruptions, all frozen hashes match, and the separate raw-only auditor reports zero errors. Otherwise retain FAIL/STOP without retry.

## C — Costs / constraints

Finite JSON on Windows host CPython, CPU only. No WSLc, Docker/OrbStack, GPU/CUDA, model, GUI, game, network call by the experiment, or user-input effect. No claim about a production caller, planner decision, gameplay, task effect, or #59 live threat-control gate.

## U — Unknowns

Whether the production caller supplies a trustworthy external binding, whether another consumer independently validates these guard fields, and whether exposing the event changes a live planner decision. This package cannot satisfy the separate #6561 WSLc gate or #59 live threat-exposure requirement.

