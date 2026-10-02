# Issue #43 AoII observation-freshness method T0 report

## Decision

Allocation `AOII-OBSERVATION-FRESHNESS-43-T0-20261001-02` ends `STOP_AUDIT_SOURCE_DRIFT`. The corrected auditor can replay the retained second candidate raw, but it is not byte-identical to the auditor source hash frozen before execution. Do not report allocation PASS.

Supplemental only: the second immutable raw has 12 deliveries over six authored cases, the corrected independent replay reports zero row mismatches and zero authority grants, and four fixed evidence mutations are rejected by the test suite. The first raw/audit mismatch and both source identities remain preserved.

## What the fixture distinguishes

- Old-but-unchanged evidence: capture age 5 ticks, no receiver/source predicate mismatch.
- Recent-but-superseded evidence: capture age 1 tick, receiver belief remains wrong for two ticks.
- Rapid reversal: same-tick explicitly correct vs stale beliefs yield different mismatch scores.
- Missing truth: UNKNOWN, not zero mismatch.
- Source-generation change: old capture is not current-generation evidence.

This is a demonstration that the offline metric can represent these distinctions in a constructed trace. It is not validation of a real GUI truth source or real planner belief measurement.

## Verification and limits

Five local unit tests pass; py_compile, SHA256SUMS, supplemental raw audit, diff-check and analysis-index check pass. Host macOS arm64 / CPython 3.14.5, standard library only. No Docker/OrbStack, GUI, model, input, network, user data, production component, task effect, or performance endpoint was used. AoII remains offline-only; the registered experiment remains STOP.
