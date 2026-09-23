# Issue #3212 — successful matched reuse/fresh recheck after runner STOP (2026-09-20)

This is additive scoped evidence after the separate benchmark STOP in #3377. It does not rewrite that failure or close the benefit HOLD.

## H/T/D/C/U

- **H:** A current receipt with a fresh gate can support repeated real application effects without relaunching the browser, while a fresh allocation still preserves the lifecycle guards.
- **T:** Docker image `mixed-formal-2992-debian:20260920` (`sha256:766abfd10382ab8b59ed793094a685481190f840d338b7bc4664ca162a2da619`), `--network none`, Xvfb, real Chromium, CDP DOM oracle. The reuse arm held one browser and executed three gated actions. The fresh arm used three independent A→B allocations with persisted receipt state and a new browser resource each time.
- **D:** Reuse: fresh gate `3/3`, DOM effect `3/3`, launch→ready `342.104 ms`, action times `17.312/7.897/6.810 ms`, reuse count 3, reacquisition count 3. Fresh: DOM effect `3/3`, old receipt rejected `3/3`, measured A→B wall time `3631/3596/3595 ms`. Raw combined SHA-256: `e1871245260d6fc64856bc082d3a3819637f895a025b979c261c566d9c79cd99`.
- **C:** `PASS_CHROMIUM_REUSE_FRESH_LIFECYCLE_SCOPED`; measured evidence supports avoiding the observed fresh allocation/restart cost in this fixture while preserving the tested effect and old-receipt rejection. This is not a complete model-wait/reacquisition-cost or production-latency claim.
- **U:** The arms are not a preregistered end-to-end model-wait benchmark: fresh wall time includes two container invocations and the reuse arm includes one. Keep `HOLD_REUSE_BENEFIT_UNMEASURED` for the full issue gate until equal-cost scheduling, changed-source, timeout/cancel, restart, and held-out cases are measured.

The committed runner, fixture, and raw JSONL are under `research/chromium/issue-3212-reuse-fresh-recheck-v1/`.
