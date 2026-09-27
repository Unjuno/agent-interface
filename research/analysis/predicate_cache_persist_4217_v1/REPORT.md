# Predicate cache persistence across restart — Issue #4236

## Disposition

**Formal allocation 01:** `STOP_EXTERNAL_EXECUTION_TIMEOUT`, scientific rows 0, no verdict. The consumed monolithic runner exceeded the surrounding 30 s execution envelope before stdout, parent-exit receipt or `FORMAL.json`; post-timeout inspection found no live study process. It was not rerun.

**Formal allocation 02:** `HOLD_AUDIT_GATE_SPEC_ERROR`. Three immutable v2 batches completed the full 48-row / 4-control scientific matrix without external timeout or row replacement. The frozen auditor reconstructs every row with `errors=[]`, candidate wrong rows 0, candidate stale hits 0 and candidate exact-key hits 6. However the preregistered gate mistakenly required 48 VALUE_ONLY hits even though only 24 of the 48 rows belong to VALUE_ONLY. Frozen audit exit=1 and formal acceptance remains HOLD.

A separately versioned postformal diagnostic, on the unchanged `FORMAL_V2.json`, uses the mathematically correct VALUE_ONLY denominator 24 and returns `PASS_POSTFORMAL_DIAGNOSTIC_ONLY`; 10/10 coherent copied-evidence mutations reject. This **does not override the formal HOLD**.

## Retained observations

| Metric | Frozen/raw observation |
|---|---:|
| total formal rows | 48 |
| malformed-artifact controls | 4 |
| dependency-bound wrong values | 0 |
| dependency-bound stale-key hits | 0 |
| dependency-bound exact-key hits | 6 |
| value-only hits | 24/24 value-only rows |
| value-only wrong values | 9 |
| value-only unsafe executable TRUE rows | 6 |
| value-only stale-provenance reuse rows | 18 |

The 18 stale-provenance rows include cases where recomputed semantic truth happens to remain equal (semantic ABA/new generation, producer replacement, source replacement). Equal value is not evidence that an old persistent artifact remains provenance-current.

## H/T/D/C/U boundary

See `PLAN.md` and `V2_PLAN.md`. The candidate serializes a deterministic `FORM_READY` predicate and exact declared dependency key. Every scored consumption occurs in a fresh Python process. SHA-256 protects artifact integrity only; it is not authentication. The declared dependency set is assumed complete, so this experiment does not solve hidden dependencies.

No GUI/input/model/provider/network experiment, task effect, token/latency benefit, crash-atomic publication, power-loss durability, concurrency, cross-platform transfer, production authority or integrated-path acceptance is claimed.

## Provenance

Current-main intake for the Issue: `16cfc7868549d07131a14194425565ffcaf70f52`.

Allocation02 formal raw SHA-256: `43b303c381eaf3a1da063fb174a3d7114aae8fc95a33504ffbc7294d3aa759a0`.
Frozen audit SHA-256: `641d3cd37de76dc869c4ca467566a40c8111266937564447894be57780d28bb3`.
Postformal diagnostic SHA-256: `f26790948f656eb3efca6f000489a2e60ea1b6300db88b69281f64d3c2552461`.
Postformal controls SHA-256: `79d13cf347c081e7626a4887b76aebc83a9e817f399f14740aa1de9b875c3a87`.
All source hashes in the original and v2 freezes rechecked unchanged after the formal allocation.

Merge only as scoped retained HOLD/diagnostic evidence. Do not close #4236 as a scientific PASS and do not promote a persistent predicate cache into runtime defaults from this result.
