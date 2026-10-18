# Issue #8569 — A01 preregistration

Allocation: `8569-prevention-conditional-a01-20261008`  
Base: `main` at `5215aab506f43c8a02470d495b7352b1326a9580`  
Runtime: Ubuntu under WSL (`wsl.exe` 3.0.1.0; Linux kernel reports `6.18.40.1-microsoft-standard-WSL2`), Python 3.12.3; network not used; no external service or GUI. WSLc 3.0.1.0 and a local pinned Python image were available, but `wslc run` returned a generic `E_FAIL` on the preflight smoke invocation. This is recorded as a runtime-launch diagnostic, not a scientific STOP; the experiment proceeds in native WSL and does not require a Docker boundary.  
Scope: exact arithmetic over the authored synthetic fixture in `trace_fixture.json`; no sampling and no empirical reliability claim.

## H / T / D / C / U

**H — hypothesis.** When prevention is more effective in the easy than hard regime, conditioning recovery on actual prevention failure shifts the demand mix toward hard cases. This can change conditional success estimates and reverse a recovery-strategy ranking. Equal-effectiveness prevention is a null-selection control; equal regime sensitivity is a ranking-invariance control.

**T — test.** Candidate computes exact rational metrics from the frozen two-regime fixture. A separately written auditor reconstructs the expected values from the fixture without importing candidate code. Both report the unconditional recovery mix, prevention-failure demand mix, conditional recovery outcomes, joint system outcomes, and a deliberately naive joint estimator. Construction tests also check four scorer mutations: swapped conditional/unconditional denominators, dropped regime, reset-to-initial demand mix, and safe-stop-as-success. The formal candidate is invoked once; then the auditor is invoked once. No reruns or retries.

**D — decision.** `PASS_METHOD_SCOPED` only if the independent audit exactly reconstructs all fractions; the primary fixture shows both the conditional/unconditional A-vs-B rank reversal and the direction of the naive-estimator error; both controls satisfy their preregistered invariants; and all four mutations are rejected. `FAIL_NO_SELECTION_EFFECT_IN_FIXTURE` if exact valid output does not show the primary selection effect and reversal. `FAIL_DENOMINATOR_OR_STATE_RESET` for denominator, regime-dropping/reset, or fabricated safe-stop scoring. `HOLD_FIXTURE_OR_ORACLE` for missing or inconsistent inputs, outputs, or independent reconstruction. No result transfers to a real application or system.

**C — competing explanations.** Existing intention-to-treat and conditional-fallback metrics may already cover this distinction; real prevention may be regime-neutral; recovery reset correctness may dominate demand selection; and a rank reversal in authored values may have no realistic analogue.

**U — limits.** Two stationary, known regimes and hand-authored probabilities only. No GUI, model, users, live failure, state restoration, runtime reliability, or product readiness. The fixture illustrates estimand behavior and method checking, not calibrated rates.

## Frozen invocation

From the workspace on Windows, using the Ubuntu distribution and this package's fixed mounted path:

```text
wsl.exe -d Ubuntu -- bash -lc "cd /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_research_8569_prevention_cond_a01_20261008/research/analysis/prevention_conditioned_recovery_8569_a01_20261008 && python3 -B candidate.py --output candidate_raw.json"
wsl.exe -d Ubuntu -- bash -lc "cd /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_research_8569_prevention_cond_a01_20261008/research/analysis/prevention_conditioned_recovery_8569_a01_20261008 && python3 -B auditor.py candidate_raw.json --output audit.json"
```

Run the first command exactly once, retain its output, and only then run the second exactly once. Construction checks must complete before the freeze commit; generated formal outputs are added afterward and are never input to another candidate invocation.
