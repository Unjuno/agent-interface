# Issue #5424 T4 — severity-ranking inversion and hard-stop control

**Allocation:** `ACTION-ERROR-BUDGET-5424-T4-RANKING-INVERSION-HOSTCPU-20261003-01`  
**Owner:** Codex research thread `01a0b990-3d17-72f1-a908-9a2072104ce5`  
**Base main:** `43f7cd88d91af05036fae2100ec4e155c59e105c`  
**Branch:** `research/5424-ranking-inversion-t4-20261002`  
**Window:** 2026-10-02 16:00–16:30 UTC  
**Execution:** Windows host CPU, Python standard library only. GPU/CUDA/model/GUI/WSL/WSLc/Docker/network are not used.

## H / T / D / C / U

- **H:** With equal 40-opportunity histories, unweighted failure count will freeze route A (eight recoverable failures) but leave route B available (one catastrophic plus one recoverable failure). The frozen ordinal-severity threshold and an independent hard-catastrophe gate will freeze B instead. In a held-out eight-offer continuation, stopping B before primary actuation will prevent its two scripted catastrophic primary effects, but a correlated fallback can still produce severe outcomes; freeze and fallback exposure must therefore remain separate.
- **T:** Freeze the finite history and two eight-step post-signal scenarios in `fixtures.json`. Compare `NO_FREEZE`, `UNWEIGHTED_COUNT`, `ORDINAL_SEVERITY`, and `HARD_CATASTROPHIC` on identical opportunities. Historical weights are `ok=0`, `recoverable=1`, `severe=4`, `catastrophic=10`; count threshold is 6 and ordinal threshold is 11. Frozen routes may resume only after two verified positive probes from the current route generation. The fallback scenarios are independent-safe and incident-correlated-severe. Candidate runs once; a separately implemented raw-only auditor runs once only if candidate exits 0.
- **D:** `PASS_METHOD_SCOPED` requires exactly 40 historical offers per route; A count/points `8/8`, B `2/11`; count freezes A only; ordinal and hard gates freeze B; all four policies preserve all 16 held-out offers per scenario; the hard gate executes zero B catastrophic primary effects; the count gate leaves B exposed to both; current-generation recovery opens at step 6 while stale/missing probes do not open in construction tests; independent-vs-correlated fallback severities are reported separately; the auditor exactly reconstructs all rows and summaries and rejects all five frozen corruption mutations. Any mismatch is retained as failure/HOLD, with no rerun.
- **C:** The fixture is deliberately finite and hand-authored. Thresholds/weights are policy choices, not calibrated risk estimates. Counterfactual primary outcomes while frozen are oracle-only and censored from policy input. A safe-looking alternative can share the incident; the hard stop is not a guarantee that the whole workflow is safe.
- **U:** This cannot estimate natural frequencies, SLOs, real-route attribution, production benefit, task/user effects, safety certification, or general policy quality. The two fallback regimes do not represent the diversity or dependence of deployed alternatives. No live route or product behavior is tested.

## Frozen execution boundary

`freeze.py` records source and fixture SHA-256 values, Python/platform identity, the exact base, owner, window, commands, and collision-guarded absent output paths. Construction tests use inline cases and do not read the formal fixture. Before candidate invocation, recheck current GitHub main equals the frozen base, verify every hash, verify both output paths are absent, confirm no working-tree changes to frozen files, and confirm current UTC is inside the frozen window. Candidate and auditor are each limited to one invocation; there are no tuning, replacement, or retry runs.

T4 is a new host-only successor to the already-retained T2/T3; it does not edit or rerun either result, T0/T1, or PR #5438. It uses no shared GPU/container lane, so it does not request or inherit a #5085 slot.
