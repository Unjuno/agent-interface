# External-transition prediction T0 — belief contracts

Status: preregistered finite-method experiment; no result is claimed until the frozen candidate and auditor each run once.

- Parent Issue: [#5368 — Action-conditioned belief contracts](https://github.com/Unjuno/agent-interface/issues/5368)
- Distinct extension: its 2026-10-02 “Unverified external-disturbance prediction test” comment; this does not repeat the original scalar/set, risk-budget, or view-updateability tests.
- Frozen base: `main@3729d6825e67b7276b58d40ef6c125e4a3b441bf`
- Branch: `research/belief-external-drift-5368-t0-20261003`
- Allocation: `belief-external-transition-5368-t0-hostcpu-20261003-a01`

## H / T / D / C / U

**H.** Predicting the set of states reachable during an unobserved interval, then intersecting it with a source-bound current observation, rejects actions made unsafe by an unobserved external transition while preserving admission when the complete transition model or a current observation leaves only safe states. A sticky last-observation belief will admit at least one unsafe case; an age-only timeout will refuse at least one safe control.

**T.** Exhaustively evaluate nine frozen deterministic traces over states A (the only state in which `approve` is allowed), B, and C. The traces cover a complete no-disturbance control, a hidden redirect, current observations of both destinations, a stale-generation observation, an incomplete/unknown transition alphabet, a compatible but out-of-support state, a current observation contradicting a claimed-complete model, and two-step reachability. Compare (1) a sticky last-observation gate, (2) an age-only timeout, and (3) the candidate reachable-set gate. A separately written auditor reconstructs every reachable set and decision from fixture plus raw output; four predeclared output-corruption controls must all be detected. The candidate receives only each case's public gate input, never the hidden truth record. No model, GUI, input, live effect, or GPU is used.

**D.** `PASS_METHOD_SCOPED` only if all nine candidate rows match the independently reconstructed reachable states and decisions, zero unsafe actions are admitted, the no-disturbance and fresh-safe-observation controls are admitted, unknown/incomplete or contradictory-model cases fail closed, all four mutation controls are detected, the sticky baseline has an unsafe admission, and the age-only baseline needlessly refuses a safe control. Otherwise retain the first outcome as `FAIL_METHOD_SCOPED`, `FAIL_AUDIT`, or `STOP` as applicable. No rerun or replacement allocation.

**C.** The change-generation invalidation route may be simpler than propagating a reachable set. A sufficiently trustworthy observation of the actual current scope may resolve uncertainty without a transition model. It may also be impossible to establish complete external-event coverage.

**U.** Deterministic synthetic states only. This does not estimate real event rates, observation trustworthiness, GUI dynamics, belief-model completeness, or action safety in a live system.

## Resource and run protocol

The experiment is finite host-CPU work. WSLc was not invoked: current coordination Issue #5085 and the latest #5368-related PR #6775 record an unresolved WSLc attribution/allocation hold. No Docker Desktop CLI is installed in this Windows shell. This protocol does not request or infer a WSLc/GPU lease. Runtime execution is local, deterministic, standard-library-only, and has no network/model/GUI/input access.

Construction check is separate from the formal run. After it passes, freeze this README, fixture, candidate, runner, auditor, construction test, and their SHA-256 values in `FREEZE.json`; commit that freeze before formal execution. Invoke `python -B runner.py` once (exclusive-create raw files), then invoke `python -B audit.py` once (exclusive-create audit). Existing outputs prohibit retries. The independent auditor does not import candidate code.
