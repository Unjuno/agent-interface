# Justification-bound ACTION_SAFE R1 - plan

Issue: #1862. Task: `JUSTIFICATION-BOUND-ACTION-SAFE-R1-20260919-001`.
Parents: #1816/#1850 (OR-of-AND justification validity/incremental maintenance) and #1829 (COMMITTED versus fresh ACTION_SAFE).
Reservation main: `7eaa6f5ffdf710e729db0abe00a3dfa617979309`.
Additive namespace: `research/analysis/justification_bound_action_safe_r1_v1/**`.

## Question

For a derived claim that had one or more valid alternative justifications at COMMIT, what exact evidence may authorize a later external action after support versions/truth values have changed?

## H

Let a declared justification family be positive OR-of-AND support sets. COMMIT records exactly the justifications satisfied at validation time and the semantic version identity of every support used by those justifications.

At a later action boundary, `ACTION_SAFE` is true iff at least one recorded commit-time justification remains fully usable: every support in that justification is still semantically version-identical to the committed support and currently true.

Consequences to distinguish on identical rows:

1. `STICKY_COMMITTED` is unsafe when all recorded justifications have broken.
2. `CURRENT_TRUTH_ONLY` is unsafe because a justification absent from the commit support set can become true later; that does not retroactively validate the old commit.
3. `ALL_COMMITTED_SUPPORTS_CURRENT` over-invalidates when one recorded alternative breaks but a different recorded alternative remains fully current.
4. A support that stays true but changes semantic version is not a valid witness for the old commit.

## T

Frozen finite universe:

- supports: `B0,B1,B2`;
- candidate justification sets: all nonempty singletons and pairs: `{B0}`, `{B1}`, `{B2}`, `{B0,B1}`, `{B0,B2}`, `{B1,B2}`;
- declared families: every nonempty subset of those six sets = 63 families;
- commit valuations: all 8 Boolean support masks, retaining only family/valuation pairs where at least one justification is satisfied;
- later support state independently takes one of `SAME_FALSE`, `SAME_TRUE`, `CHANGED_FALSE`, `CHANGED_TRUE` for each support;
- formal corpus: every retained family/commit pair x all `4^3=64` later states;
- candidate uses bit-mask implementation; oracle independently reconstructs named support sets/version identities;
- comparators: sticky commit, current truth only, all committed supports current;
- directed controls: newly true uncommitted alternative; one stale committed alternative with another survivor; all committed alternatives stale; recorded support version mutation.

Construction is excluded from formal evidence and uses only family masks 1..8 plus the four directed controls. Source/readback freeze occurs before the only full formal invocation.

## D

`PASS_JUSTIFICATION_BOUND_ACTION_SAFE_SCOPED` iff:

- full formal row count is 20,928;
- candidate/oracle mismatch = 0;
- candidate unsafe admits versus oracle = 0;
- candidate false rejects versus oracle = 0;
- candidate ACTION_SAFE without a fully current recorded justification = 0;
- stale-all-recorded candidate admits = 0;
- newly-true-uncommitted candidate admits = 0 and such discriminator rows exist;
- surviving-committed-alternative rows exist;
- sticky unsafe admissions >0;
- current-truth-only unsafe admissions >0;
- all-committed-supports-current false rejections >0;
- all four directed controls pass;
- independent audit and four result-corruption controls pass;
- formal1/reruns0/replacements0/post-freeze-tuning0.

Any unsupported action admission => `FAIL_ACTION_SUPPORT_LAUNDERING`. Any false rejection despite a fully current recorded justification => `FAIL_ALTERNATIVE_SUPPORT_OVERINVALIDATION`. Integrity contradiction => `FAIL_INTEGRITY`.

## C

This theorem assumes semantic support-version identity is trustworthy and complete. If support provenance is incomplete, version equality is forged, or a dependency is omitted, the contract can be unsound. Negative/defeasible/probabilistic support, cycles, concurrent commit mutation and cross-claim transactional isolation require richer semantics.

## U / stop

Deterministic finite analytical model only. No stochastic sampling uncertainty, runtime ABI, GUI/model/task result, latency, token, memory, or product claim. The dominant uncertainty is specification adequacy, not measurement noise. Stop after the first source-frozen formal result and audit.
