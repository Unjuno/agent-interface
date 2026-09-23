# Historical persistent efficiency wrapper SCOPE_MISMATCH repair v2

## Decision

**PASS_HISTORICAL_PERSISTENT_SCOPE_REPAIR_SCOPED**.

This is the corrected source-first successor to the procedural stop retained in Issue #790. The scientific space here is new: seven tasks with every `2^6 = 64` inter-task stable/restart transition sequence. No six-task row from #790 is reused.

## Why this rung exists

Issue #57 retained a real-X11 cross-layer result showing that one caller-owned binding generation should feed both runtime program freshness and target-handle scope. Issue #774 then exhaustively established the generic caller/cache composition rule. The historical integrated-efficiency wrapper still had one concrete mismatch: its target-handle check maps `MISSING -> no_match`, but a runtime `SCOPE_MISMATCH` becomes raw `scope_mismatch`, while the exact adaptive caller only accepts typed stop reasons and the persistent route repairs only `no_match`.

The historical path is therefore already fail-closed, but a generation change can become `CALLER_FAILED` rather than entering the existing typed stale/repair route.

## Frozen H / T / D / C / U

**H.** Three semantic line changes are sufficient: normalize `SCOPE_MISMATCH -> stale` at reuse and final target checks, and include `stale` in the persistent `repair_on` list. Stable reuse should remain model-free; every generation transition should invoke exactly one existing repair/model stage before execution; no stale alias should reach execute.

**T.** The exact historical `run_integrated_efficiency_live_v1.py` Git blob `af12b8bbdf11c2c2c9f92fba94646cdc1357f7d8` and exact `adaptive_acquisition_caller_v2.py` blob `176b342913ea6b5b704d4c986d5ddbf1dbcd8169` were frozen. Candidate patch blob `05f94b8eed75e0901dfc9be5f30bc525fd66e1fc` changes only the two status normalizations and `repair_on`. It reconstructs the candidate byte-exactly (candidate blob `9b128d4ccd6df8f03dc7a238914ce01232190888`).

A deterministic RuntimeClient-interface fixture preserves aliases/pixels/geometry and advances only caller generation. Cached aliases then return `SCOPE_MISMATCH`; a fresh mint binds aliases to the new generation. The exact historical/candidate `run_task` functions are invoked directly. Deterministic model fixtures exercise accounting/repair branches but are not model-quality evidence.

Before formal, GitHub retained the source archive and FREEZE with zero seven-task traces executed. A placeholder source-file publication mistake is preserved in FREEZE: commit `ce3b5b1757ec0ae1f37bb003ae70b5e9bea7a32f` wrote `PLACEHOLDER`, then commit `7d1ca1cbeaeef85cd66baa0d7796af47cc86b6e6` replaced it with the exact archive before any scientific trace.

Formal: one invocation over all 64 six-bit transition sequences, two arms, seven tasks/trace = **896 exact `run_task` executions**. No rerun, replacement, extension or tuning.

**D.** Candidate PASS required 448/448 `TASK_SUCCEEDED`, zero `CALLER_FAILED`/safe stops/stale executes, exactly 192 `expanded_model` repairs for the mathematically expected 192 restart events, and zero repair/model calls on stable reuse. Historical comparator was frozen to 127/448 success, 321/448 `CALLER_FAILED`, repair0, stale execute0, with all 63 restart-containing traces exposing failure. Cold anchor fixture calls were 64/arm.

**C.** Full runtime destruction may report `MISSING`, which historical code already repairs. This test isolates the narrower same-observable-surface generation mismatch retained by #57. The historical allocation-specific `repair_required = index == 3` report hint is not scored; the audit reads actual adaptive model ledgers and outcomes.

**U.** Deterministic exact-wrapper integration only. No Chromium/X11 lifecycle detection, provider/model quality, actual token/full-wall-time economics, UI task effect, check-to-input atomicity or production reliability is measured.

## First formal outcome

| Metric | exact historical wrapper | three-line candidate |
|---|---:|---:|
| traces | 64 | 64 |
| `run_task` executions | 448 | 448 |
| `TASK_SUCCEEDED` | 127 | **448** |
| `CALLER_FAILED` | **321** | **0** |
| safe stops | 0 | 0 |
| repair `expanded_model` calls | 0 | **192** |
| cold `anchor_model` calls | 64 | 64 |
| stale alias reaches execute | 0 | **0** |
| restart events | 192 | 192 |
| restart-containing traces | 63 | 63 |

The historical comparator remains safe in this fixture: stale aliases do not execute. Its failure is typed-integration/liveness: once the first `SCOPE_MISMATCH` appears, raw `scope_mismatch` is unsupported by the exact adaptive caller and the route returns `CALLER_FAILED`; because the cache is never repaired, later tasks in that trace continue failing even across stable intervals.

The candidate maps the mismatch to the already-supported `stale` reason. Every one of the 192 restart events triggers exactly one `expanded_model` repair, fresh mint/rebind, final revalidation and successful execution. Same-generation reuse triggers no repair/model stage.

This demonstrates that the historical wrapper does not require a new repair mechanism; it requires a small translation at its target-check boundary plus admission of `stale` into the repair reasons.

## Audit and corruption controls

The source-frozen independent auditor parses every raw trace, derives the expected success/failure count from the position of the first restart for the historical arm, checks candidate repair stages against every transition bit, recomputes aggregate counts, and verifies full 64-sequence binary coverage.

Frozen audit: **PASS**, errors0. Formal result SHA-256 `991208d020d92c7d0e74c4ead970e1d312fcaec6c822090f9b71a9b776ebd121`; raw trace SHA-256 `ab155b1d796c5d02900248735e9819c3ca71345f41df7d3431de44f167a8f86b`; audit-result SHA-256 `42100b7a1849ac4b3f0df69c358c86bb72a3192d574e2129c7b366e3f835a08e`.

Six copied-evidence mutations were all rejected: candidate aggregate success mutation, stable-path repair insertion, candidate `CALLER_FAILED` insertion, erased historical failure, missing trace row, and duplicate/missing trace coverage.

Postformal source hashes remain identical to FREEZE, and applying the frozen patch to the pristine historical source reconstructs the candidate SHA/Git blob exactly.

## Procedural predecessor

Issue #790 is deliberately not upgraded into formal evidence. Its first harness invocation accidentally consumed its whole planned six-task/32-sequence space before remote source publication. That diagnostic remains retained and #790 was closed `not_planned`. This v2 result uses a disjoint seven-task/64-sequence space after source-first remote freeze.

## Integration boundary

This closes the wrapper-specific mechanism gap exposed by #57/#774 at deterministic scope. It does **not** by itself modify shared runtime or establish second-domain actual-model economics. The next #57 step remains an actual supported authenticated model/full-wall-time evaluation when such a path is available; synthetic usage must not substitute for it.
