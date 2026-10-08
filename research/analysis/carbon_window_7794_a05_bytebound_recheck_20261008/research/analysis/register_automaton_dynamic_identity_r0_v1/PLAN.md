# Register automaton dynamic identity R0 — plan

Parent: GitHub Issue #1712. Successor Issue: #1826. Related operational boundary: #45.
Task: `REGISTER-AUTOMATON-DYNAMIC-IDENTITY-R0-20260919-001`.
Base: `c5f15e7c254d36a1f8ab29b364b6430a6925eb36`.
Additive publication path: `research/analysis/register_automaton_dynamic_identity_r0_v1/**`.

## Question

When an action binding is valid only while both an interface generation and target identity remain unchanged, can exact behavior be represented without retaining those dynamic values, or does a register-style abstraction provide the minimal symbolic boundary?

## H

For finite nonempty generation domain `G` and target domain `T`, after `BIND(g,t)` a later `USE(g',t')` is valid exactly when `g'=g` and `t'=t`.

1. Every bound pair `(g,t)` is behaviorally distinguishable from every other bound pair, and `UNBOUND` is distinguishable from every bound pair. A literal deterministic no-register FSM therefore needs at least `|G|*|T|+1` states; the direct concrete construction reaches the bound.
2. A typed two-register automaton with control states `UNBOUND`/`BOUND` plus registers `r_G,r_T` exactly implements the same predicate for arbitrary values and is equivariant under independent renaming of both domains.
3. `GENERATION_ONLY`, `TARGET_ONLY`, and `CONTROL_ONLY_ACCEPT` each admit unsafe uses once their omitted identity dimension has at least two values.

## T

- prove the lower bound and the two-register construction directly;
- freeze `PLAN.md`, `PROOF.md`, `formal.py`, and `audit.py` before formal execution;
- one formal invocation over every domain-size pair `1..16 x 1..16` and every bound/query pair, totaling 2,238,016 cases;
- compare `TWO_REGISTER`, `GENERATION_ONLY`, `TARGET_ONLY`, and `CONTROL_ONLY_ACCEPT` against the exact equality oracle;
- independently test equivariance under all independent permutations of a `3 x 3` witness domain;
- independent audit re-derives the enumeration without importing candidate functions;
- corruption controls mutate one summary count, the streamed row digest, and one lower-bound witness;
- formal invocations `1`, reruns `0`, post-freeze tuning `0`.

A development-only dry run was used to debug the auditor before this source freeze. It is not a retained formal result.

## D

`PASS_REGISTER_AUTOMATON_IDENTITY_SCOPED` iff:

- `TWO_REGISTER` mismatch count is zero;
- each reduced policy has at least one unsafe accept;
- equivariance mismatches are zero;
- all lower-bound witness counts match the analytic construction;
- independent audit has zero errors;
- all three corruption controls are detected;
- source/result integrity passes.

Any two-register mismatch is `FAIL_REGISTER_AUTOMATON_IDENTITY`. Any source/result/audit inconsistency is `FAIL_INTEGRITY`.

## C

The theorem concerns exact equality-sensitive identity. Equivalent typed tuple storage elsewhere is semantically the same retained data, not evidence that the values are unnecessary. Order, arithmetic, aliasing, probabilistic transitions, learning, and richer interface semantics may require stronger models.

## U

Finite equality-only semantics. No claim of total memory-bit compression: registers still store dynamic values. No natural ID distribution, latency/token gain, automatic automaton learning, GUI/backend transfer, or production ABI claim.
