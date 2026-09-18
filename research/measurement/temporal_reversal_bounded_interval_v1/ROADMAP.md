# TEMPORAL-REVERSAL-BOUNDED-INTERVAL-R1-20260918-006

Issue: #1311
Formal budget: exactly one invocation; no rerun/replacement/tuning.

H: estimator only. Compare STRICT_EXACT vs BOUNDED_INTERVAL on identical 10 Hz, one-reversal, ±1000 micro-unit per-sample jitter traces.
T: formal ages {25,50,75,100,150,200} ms × post directions ±1 × phases 0..99; both estimators; 2400 rows.
D: PASS_BOUNDED_INTERVAL_JITTER_RECOVERY_SCOPED only if all frozen gates in Issue #1311 pass.
C: known hard error bound/unit speed/one reversal may be false in real systems.
U: synthetic only; UNKNOWN has no action/current authority.

Construction uses nonformal ages 40/110/175 ms and half-millisecond phases only.
