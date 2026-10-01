# MAP01 recovery visual-context guard — supervised repair

Task `MAP01-RECOVERY-VISUAL-CONTEXT-GUARD-20260917-002`, Issue #575.

## Decision

**`PASS_VISUAL_CONTEXT_GUARD_SCOPED`**.

The repaired formal block changed only the outer execution envelope relative to consumed #568 ID001. The science source, eight-case schedule, runtime artifact, fixture, seed, recovery/coast programs, baseline health/ammo/current-age contract, threshold `0.015`, audit and decision gate were held fixed.

A long-lived container process was launched once and polled externally. It completed all 8/8 cases with exit code 0. No formal retry, resume, replacement or extension occurred.

## Result

| pair | coast MAE | coast guard | recovery MAE | recovery guard |
|---:|---:|---|---:|---|
| 1 | 0.0143970326 | ADMIT | 0.0273892563 | REJECT_CONTEXT_CHANGED |
| 2 | 0.0143980030 | ADMIT | 0.0336008966 | REJECT_CONTEXT_CHANGED |
| 3 | 0.0133540342 | ADMIT | 0.0383865796 | REJECT_CONTEXT_CHANGED |
| 4 | 0.0143980030 | ADMIT | 0.0386388749 | REJECT_CONTEXT_CHANGED |

The unchanged baseline contract returned `VALID_CURRENT` in all 8 cases. The one added visual dependency cleanly separated this finite fixture: all four coast controls stayed at or below `0.015`, and all four recovery cases exceeded `0.015`.

All eight cases retained health 97 and ammo 48, completed normally, ended with verified empty key/button state, and independently scored 0 kills / 0 deaths / no map exit.

## Interpretation

This closes the narrow blindspot exposed by #551 for this fixed fixture: an explicit planner-visible context dependency can reject recovery-induced frame drift that health/ammo/current-age validity alone does not notice.

It does **not** establish that full-frame RGB MAE is the correct production representation. A changed frame may be harmless to a particular action, while harmless animation/render jitter may cause false rejection elsewhere. Therefore this result supports the architectural requirement for context binding, not promotion of `MAE <= 0.015` as a universal runtime rule.

The next high-information rung should keep recovery and admission semantics fixed and compare fail-closed context rejection with exactly one bounded reanchor/fresh-observation path. Only after that should model-in-loop recovery be consumed.

## Evidence / error check

- frozen formal audit: `PASS_VISUAL_CONTEXT_GUARD_SCOPED`
- frozen audit result SHA-256: `ffb269d10599d3085bbb8e2f59a856d506d6b2b68063cebc58c6cc3f8b88f314`
- exact formal summary SHA-256: `e3b62aaf9fd714f0b042e00c1fa2408b92acfc25f72c7dc441813cc3040110d3`
- formal stderr: 0 bytes
- audit stderr: 0 bytes
- postformal source/image/release/score reconstruction: PASS, zero errors
- pre/post contract tests: 4/4 PASS
- offline runtime artifact SHA-256: `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`
- scientific source is byte-identical to #568; only task/base identity and supervision changed in ID002.

Full-frame archive is retained locally/conversation-side; GitHub publication should not claim binary raw retention unless it is actually uploaded and read back.
