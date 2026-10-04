# Issue #7728 Windows counter cross-check A02

## Result

The raw sensor/counter audit returned `PASS_SIX_SAMPLE_COUNTER_ORACLE_MATCH`: all six consecutive `NumberOfItems64` samples for `RAPL_Package0_PKG` were strictly increasing and inside the EMI v2 package-channel endpoint readings; both EMI endpoints declared unit code 0 (picowatt-hours). The independent auditor rejected all three mutations: wrong EMI unit, an out-of-bracket counter sample, and a dropped energy sample.

The raw counter moved from `723609618665000` to `723637170789166` across the six samples. Consecutive sample increments ranged from `5237121112` to `5795677777` picowatt-hours, with five distinct observed increments. The bracketed EMI energy delta was `39630564722` picowatt-hours over `72701864` units of 100 ns. This increment variability is observed package consumption; it does not identify the meter's least count or establish its hardware resolution.

Six accompanying total-CPU samples averaged 81.629% (range 72.311%–96.240%). This characterizes the busy ambient host. No load was generated, and no application, GUI, model, route, or task was run.

## Provenance deviation

The preregistration froze local `origin/main` at `02e0b19838ef87dba421480154314fa07b00a386` (committed 2026-10-04 19:11:46 UTC). GitHub's current commit history shows main had already advanced to `d1a19b6929569a291c210a680c7e22c31732b949` at 19:15:04 UTC, before the 19:18:54 UTC freeze. The selected local remote-tracking ref was stale. The frozen source hashes and raw measurement remain intact, but the requirement to freeze against current main was missed. `PROVENANCE_DEVIATION.md` records the evidence. Accordingly, report the live sensor observation as an instrument-level six-sample PASS and the current-main protocol execution as `HOLD_BASE_SNAPSHOT_STALE`; do not promote this to a current-main T0 readiness result.

## Scope

This is a Windows-host-specific repeatability check of cumulative sensor/counter compatibility, beyond A01's one in-bracket sample. It does not establish hardware resolution, a quiet idle baseline, boundary repeatability for GUI tasks, process attribution, an independent effect oracle, energy per verified effect, non-inferiority, or T1 eligibility. It does not alter the separate macOS `HOLD_ENERGY_SENSOR_UNAVAILABLE`.

The frozen source/SDK hashes are in `FREEZE.json` and `SHA256SUMS`; one candidate output is in `raw-a02.json`, one independent audit is in `audit-a02.json`, and output hashes are in `OUTPUT_SHA256SUMS`. Three synthetic auditor tests passed before freeze; PowerShell source parsing and C# compilation passed. No privilege escalation or generated workload was used.
