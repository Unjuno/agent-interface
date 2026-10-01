# Issue #5870 T0 — online rent-or-compile boundary

Allocation: `RENT-COMPILE-5870-T0-20261001-01`  
Frozen main: `da7770df8bd896738a8a7e0ccc8ea45e10b3e645`  
Additive path: `research/analysis/rent_compile_5870_t0_v1/`  
Branch: `research/rent-compile-5870-t0-20261001`

## H / T / D / C / U

**H.** On the frozen no-invalidation, correctness-qualified cost grid, the horizon-blind `RENT_THEN_COMPILE` threshold strictly lowers the maximum prefix cumulative regret versus both `DIRECT_ALWAYS` and `COMPILE_IMMEDIATELY`, where regret is online policy cost minus the exact clairvoyant minimum at that prefix.

**T.** Exhaustively simulate all prefixes 1–30 for six frozen integer-cost configurations. Direct-unit cost, setup+validation cost, and guarded-unit cost share abstract cost units; they are not mixed with tokens, time, or money. The online policy observes realized per-use cost and compiles before the next use once cumulative direct-versus-guarded premium is at least setup cost. Qualification is an explicit precondition. Candidate emits only a hash-bound per-use event ledger; an independently written standard-library auditor recomputes all event costs, every prefix, offline minima, regrets, eligibility behavior, and four corruption controls. Candidate and auditor each run exactly once after the remote source freeze; no retry or tuning.

**D.** `SUPPORT_PURE_CASE_SCOPED` only if every eligible positive-saving configuration has strictly lower worst-prefix regret than both baselines, every raw row and cost agrees with the independent oracle, unqualified and non-saving configurations never compile, and all four corruption controls reject. `FAIL_ONLINE_VALUE_PURE_CASE` if any eligible positive-saving configuration fails either strict comparison. `STOP_AUDIT_OR_SOURCE_DRIFT` for source/hash or audit-integrity failure. The label is about this finite abstract-cost subcase only.

**C.** Deterministic finite arithmetic, six hand-authored cost configurations, one host Python process per candidate/audit, standard library only. Docker Desktop was rechecked read-only: the CLI is installed but `com.docker.service` is stopped/manual and Engine version lookup times out; no container inventory is available. This T0 uses host CPU because a container is not currently usable; no service start or container operation is attempted.

**U.** No GUI task, actual compile/setup/validation cost, measured route latency/tokens, stochastic costs, forecast, invalidation, repair, endogenous demand, multi-task dependence, user benefit, or safety/effect claim. No classical competitive guarantee is transferred to the real interface. The simulator cannot establish a deployable acquisition policy.

## Frozen policy and scope

For each qualified configuration, start uncompiled with premium zero. Each direct use adds `max(0, direct_unit - guarded_unit)` to observed cumulative premium. Before the following use, compile iff the configuration is qualified and accumulated premium is at least setup cost. After compilation, pay guarded-unit cost per use. Unqualified and non-saving cases remain direct. The policy receives no sequence-length/horizon field; the fixture's 30-use limit bounds observation only. The offline comparator may choose direct forever or pay setup immediately, with complete prefix costs. Invalidation/adversarial lifecycle cases are intentionally deferred to a later rung and cannot be silently inferred from this pure case.

## Construction / freeze discipline

Construction tests exercise pure helper functions and corruption rejection; they do not emit or consume formal raw rows. Freeze exact main, fixture and source hashes in `FREEZE.json` before the one candidate call. Preserve the first candidate/audit outcome, including FAIL or STOP. After execution, publish this directory additively and keep Issue #5870 open unless the bounded experiment's stated question is fully resolved.
