# MAP01 v6 planner-window arithmetic audit — T1 result

**Issue:** #6220 (successor to closed #1632; parent research objective #59)  
**Disposition:** `PASS_WINDOW_ARITHMETIC_AUDIT_SCOPED`  
**Execution:** one synthetic candidate invocation; one independent raw-only audit invocation; zero retries  
**Frozen main:** `14b81dd1f6853623a694266b98538f812847257a`  
**Frozen package commit:** `20eaab9e450e4f36f0b6d4adc7f2fb687ec5f02a`

## Result

The unchanged v6 boundary-audit wrapper returned `PASS_MECHANISM_ONLY` with no boundary failures for the six clean synthetic arm summaries. Its v4 dependency was a deliberate stub returning a declared PASS-shaped value; this exercised only the unchanged v6 wrapper's boundary checks, not the full v4 scientific audit.

The separately authored raw-only checker returned `PASS_WINDOW_ARITHMETIC_AUDIT_SCOPED`. It verified six records (3 pairs × coast/recovery), the exact phase string, integer endpoints, and `duration_ns == end_ns - start_ns`. Each of six isolated in-memory `duration_ns += 1 ns` controls was rejected with exactly that arm's duration-mismatch finding (6/6); five additional type/endpoint/phase construction controls passed.

The explicitly out-of-scope self-consistent 3.6-second interval had no arithmetic error and passed this narrow predicate. It is retained as `OUTSIDE_CLAIM_NO_UPPER_DURATION_BOUND`, not hidden or counted as an audit miss: no maximum-duration threshold was preregistered. Therefore this T1 result cannot rule out a self-consistent window that includes delayed clock sampling or cleanup.

## Commands and receipts

Construction regressions, run before the freeze commit and unchanged afterward:

```powershell
python research/doom/map01_recovery_v6_window_integrity_1632_t1_20261002/test_audit_raw.py
python -m py_compile research/doom/map01_recovery_v6_window_integrity_1632_t1_20261002/candidate.py research/doom/map01_recovery_v6_window_integrity_1632_t1_20261002/audit_raw.py research/doom/map01_recovery_v6_window_integrity_1632_t1_20261002/test_audit_raw.py
```

Both commands exited 0; construction regressions were 3/3 PASS. After commit `20eaab9` froze the source and hashes, the candidate and auditor were each invoked exactly once:

```powershell
python research/doom/map01_recovery_v6_window_integrity_1632_t1_20261002/candidate.py --out research/doom/map01_recovery_v6_window_integrity_1632_t1_20261002/out/t1-01
python research/doom/map01_recovery_v6_window_integrity_1632_t1_20261002/audit_raw.py research/doom/map01_recovery_v6_window_integrity_1632_t1_20261002/out/t1-01/candidate.json --out research/doom/map01_recovery_v6_window_integrity_1632_t1_20261002/out/t1-01/audit.json
```

Candidate: exit 0; six arm summaries; v6 decision `PASS_MECHANISM_ONLY`; zero boundary failures.  
Independent audit: exit 0; `PASS_WINDOW_ARITHMETIC_AUDIT_SCOPED`; failures=0; mutations rejected=6/6.  
Raw artifacts: `out/t1-01/candidate.json`, `audit.json`, and six `arm-summary.json` files; SHA-256 values are in `SHA256SUMS`.

Post-run package verification independently matched the candidate's recorded v6 source SHA-256 to the frozen source and compared all six on-disk arm summaries byte-semantically against the candidate records (6/6); the audit receipt fields also matched. The 13-file SHA256SUMS manifest verified completely.

The v6 source predicate was inspected and requires a positive integer duration plus the phase label but does not compare duration to the retained endpoints. This run did **not** invoke the v6 wrapper separately on each corrupted arm; mutation rejection is evidence from the independent raw-only checker. Candidate's declared v4 stub also means the v6 clean PASS is boundary-wrapper plumbing evidence only.

## H / T / D / C / U disposition

- **H:** Supported at the narrow wrapper/source level: v6's visible predicate has no endpoint arithmetic comparison; the additive checker detects isolated summary inconsistencies.
- **T:** Frozen synthetic record condition, six matched arm summaries, one unchanged v6 wrapper invocation, one independent raw audit and six +1 ns mutation controls. No container, model, game, GUI, GPU, network, or input.
- **D:** PASS for truthful internal arithmetic, exact phase label, and 6/6 isolated corruption rejection. No PASS is claimed for a maximum-duration bound.
- **C:** This checks summary self-consistency only; it does not authenticate clocks, execution order, runtime event provenance or the real elapsed planner interval. A self-consistent 3.6 s window remains accepted by this narrow predicate.
- **U:** Synthetic audit-integrity only. It establishes no recovery efficacy, physical held occupancy, first useful feedback, task effect, safety, survival, MAP01 progress/exit, frontier-model benefit or product performance.

Windows host CPython 3.12.10 / CPU was used. Docker Desktop's service was observed stopped; the engine was unavailable in recent checks. No service or container was started, and no formal/live allocation was consumed. The analytical fixture is deterministic and standard-library-only; this is not a Docker result.

## Follow-up boundary

Any future audit that claims to reject cleanup-contaminated elapsed windows must freeze a defensible upper-duration rule or an independently retained timer-completion/clock-boundary witness. This report does not select that rule and does not authorize v6 formal execution. Preserve #1632 and the v5/v6 outcomes unchanged.
