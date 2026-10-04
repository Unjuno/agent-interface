# Issue #59 A03 — paired health/ammo frame identity

## H / T / D / C / U

**H.** The A02 composition can preserve a renewable fire cover using individually valid health and ammo values from different observation epochs. Requiring a common sequence, capture timestamp, and binding before evaluating either guard will invalidate mismatched pairs while preserving coherent positive-ammo samples.

**T.** Freeze the current-main generic signal guard and a synthetic fixture. Run one host-side construction probe against six cases: coherent positive values; health newer than ammo; ammo newer with zero; equal sequence with unequal capture time; equal sequence/time with different binding; and coherent zero ammo. Independently audit expected decisions directly from the fixture.

**D.** Pass only if coherent positive health/ammo preserves the existing policy, every mismatched pair requests a new decision before either guard can preserve it, and coherent zero ammo requests a new decision. The independent raw-fixture auditor must pass every case and verify no input authority is granted.

**C.** Exact equality may be too strict for a runtime that intentionally emits separate per-signal captures; such a runtime needs an explicit shared frame identity or a separately justified bounded join. A synthetic identity check does not prove the controller delivers the signals together or that cancellation releases keys.

**U.** Construction evidence only. No Doom controller integration, live game, model, GUI, OS input, physical release, useful feedback, task progress, or formal allocation was exercised. A live allocation still requires its own assignment and current source freeze.

## Outcome

See `REPORT.md`, `RESULT.json`, and `AUDIT.json`. The previous A03 inline counterexample on Issue #59 showed that the A02 composition preserved an older positive ammo sample (`sequence=2`) together with a newer healthy sample (`sequence=3`). This package tests a fail-closed paired-frame gate against that counterexample and neighboring identity mutations.
