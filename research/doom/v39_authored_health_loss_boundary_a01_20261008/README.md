# V39 authored health-loss boundary A01

This one-shot construction probe asks whether current V39's **authored** health-loss guard would invalidate a fire-cover policy when visible health falls from 100 to 84 during a pending answer. The motivating triage associates that health change with a surrounding slow-answer/cover window but explicitly cannot localize when damage occurred. The probe does not reconstruct that run or infer that its cover had any particular authored threshold.

The candidate extracts and executes the frozen current-main `guard_spec`, `build_cover_monitor`, and paired monitor code against synthetic typed observations, with the frozen `ObservableSignalGuard`. It sweeps every integer `maximum_health_loss` from 0 through 20, and tests health 84, the exact computed hard floor, and one point below the floor. The separate auditor checks source/blob/hash provenance and independently reconstructs all 21 rows from strict-below threshold arithmetic. Mutation tests cover result identity, threshold, status, authority, and row-count claims.

## H/T/D/C/U

- **H:** The authored hard floor is `max(critical_health_minimum, source_health - maximum_health_loss)`. For source health 100 and critical floor 80, health 84 should request a new decision when maximum loss is at most 15, and remain within the policy envelope when the loss is 16–20.
- **T:** Run `python -B candidate.py` once, then `python -B audit.py`, then `python -B -m unittest -v research.doom.v39_authored_health_loss_boundary_a01_20261008.test_audit`. Source commit and all input identities are pinned in `FREEZE.json`.
- **D:** `PASS_CONSTRUCTION_BOUNDARY` only if the actual current-main builder/monitor produces the expected hard/soft/unchanged classifications across all 21 settings and no case grants input authority.
- **C:** A paired-signal, source-binding, strict comparison, or controller-wiring defect could prevent the expected classification. The test exercises the current source helper path rather than a manually assembled guard floor.
- **U:** Synthetic observations do not establish actual threat onset, real HUD extraction timing, model-wait latency, key-up timing, useful feedback, cancellation efficacy, recovery, survival, or task effect. The 100→84 association does not localize damage to the pending-answer interval.

## Result

`PASS_CONSTRUCTION_BOUNDARY`. The current frozen builder and paired monitor classified the triage value 84 as `HARD_INVALIDATED` for maximum-loss limits 0–15, and `SOFT_CHANGED` for limits 16–20. For every tested setting, the exact floor was preserved (or unchanged when the floor was the source value 100), while one point below the floor requested a new decision. No tested outcome granted input authority. The independent auditor reconstructed all 21 settings, and its corrected audit binds the exact committed `RESULT.json` bytes with SHA-256 `9f93737993ed42698432dfff9e797b29a318a7d888bff43b472f485b5a2cfa3e`.

## Audit hash correction

The first embedded audit is preserved byte-for-byte as `AUDIT_A01.json`. Its recorded result digest `70ec5c1f261c08629f9880c60dc9b99e524768ea38bff930c701db5da33ee30c` matches the LF-normalized JSON content, while the committed CRLF `RESULT.json` bytes hash to `9f93737993ed42698432dfff9e797b29a318a7d888bff43b472f485b5a2cfa3e`. The corrected `AUDIT.json` binds those exact committed bytes. `RESULT.json` itself is unchanged; a regression test checks both digests and their encodings.

This does not identify the authored threshold in the historical attempt or show when a real HUD reading would reach the monitor. A live threat exposure with per-key release, independently useful feedback, bounded recovery, progress/ammo, and terminal outcome remains required; no allocation or private game lane is granted by this package.


## Versioned package manifest

The original stale manifest is preserved byte-for-byte as `MANIFEST_A01.json`. `MANIFEST.json` is version 2 and the package test verifies exact file coverage, byte counts, and SHA-256 values for every listed file. The manifest intentionally excludes itself to avoid a recursive hash.
