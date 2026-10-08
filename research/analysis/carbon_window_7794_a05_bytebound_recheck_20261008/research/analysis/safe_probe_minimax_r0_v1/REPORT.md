# Safe-probe minimax version-space R0 — retained result

Issue #1836. Parent idea #1716.

## Disposition

**PASS_SAFE_PROBE_MINIMAX_VERSION_SPACE_SCOPED**

Formal1 / reruns0 / replacements0 / tuning0.

## Analytical contract

For a finite deterministic hypothesis set H and an explicitly authorized safe-probe set P_safe, each probe partitions H by observable output.

For one-step robust identification with no trusted prior, choose the safe probe that minimizes the largest possible surviving cell:

[
p^* = argmin_{pin P_{safe}} max_o |{hin H: output(h,p)=o}|.
]

Unsafe probes are excluded before information scoring. If no safe probe exists, the result is `NO_SAFE_PROBE`; the selector never falls back to an unsafe probe.

## Formal result

- exhaustive profile-pair comparisons through version-space size16: **51,742**
- deterministic random multi-probe cases: **250,000**
- candidate/oracle mismatch: **0**
- unsafe probes selected: **0**
- empty-safe cases: **5,000**, all fail closed
- output-label permutation changes: **0**
- entropy-baseline worse-worstcase cases: **9,633**

Directed discriminator:

- safe probe A partition: `[4,1,1,1,1]`
- safe probe B partition: `[3,3,2]`
- minimax chooses B, worst residual **3**
- uniform entropy chooses A, worst residual **4**

The entropy comparison is implemented exactly with integer `Π c_i^{c_i}`, which is equivalent to maximizing Shannon entropy for fixed version-space size because
[
H = log n - rac{1}{n}sum_i c_ilog c_i.
]
This avoids floating-point ranking ambiguity.

A perfect but unsafe probe is ignored in the directed control.

Primary audit passes five corruption controls. Independent audit regenerates the250,000-case random corpus from the frozen seed and imports no candidate/formal module.

## Retained preformal defect

The first construction used floating-point entropy accumulation in candidate and auditor through algebraically equivalent but numerically different summation expressions. Candidate/oracle minimax safety checks passed, but the independent entropy discriminator count/digest differed.

Formal remained0. Before source freeze, entropy ranking was replaced by exact integer-product ordering. Scientific H/D, seed, safe envelope and minimax selector were unchanged. Construction then passed both audits.

## Execution-envelope note

The one formal invocation completed and wrote `FORMAL_RESULT.json` plus the primary audit. The enclosing shell command then hit the45s tool limit while the independent audit was still running. The formal was not rerun. The independent audit was subsequently executed as a read-only audit over the retained result and passed.

## Interpretation

For a no-prior robust objective, safe active probing should optimize the worst remaining ambiguity, not merely expected information gain.

This does **not** say entropy is generally wrong. With a calibrated prior and expected-case utility, entropy/Bayesian criteria can be the appropriate objective. The result distinguishes the objectives and makes the safe envelope lexically prior to informativeness.

## Scope

One-step deterministic hypothesis identification only. No multi-step planning, stochastic outputs, probe cost, real GUI semantics, reversible-action proof, model quality, latency or production runtime claim.

## Next legal rung

Either:

1. derive a finite-horizon cost-aware safe-probe planner that preserves the safe envelope; or
2. transfer the one-step selector to a controlled observation-only capability/focus-query fixture.

Do not use destructive probes merely because they are informative.
