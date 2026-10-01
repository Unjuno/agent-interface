# Issue #6216 T0 — absolute outcomes alongside recovery-choice agreement

Allocation: `RECOVERY-ABSOLUTE-OUTCOME-6216-T0-HOST-20261002-01`

Frozen base: `14b81dd1f6853623a694266b98538f812847257a`

Frozen source commit: `88b54ab3770368dcd5b14c367106e0e742b0f54c`

Disposition: **`METHOD_PASS_SCOPED`**

## Question and method

Issue #6216 asks whether winner-set agreement alone can make a consistently chosen but ineffective recovery action look high quality. The primary source, Xu et al., [*Same Winners, Different Success Rates*](https://arxiv.org/abs/2609.34215), reports an ordinal symmetry for equal-cost Bernoulli candidates: regimes `(0.9, 0.8)` and `(0.2, 0.1)` have identical best-action-set distributions at every sample size despite very different absolute success.

This T0 used exact integer arithmetic for matched samples per candidate `n ∈ {1,2,3,5,10,20,50}`. The candidate computes two binomial count distributions and compares every pair of success counts. A separately implemented raw-only auditor instead convolves the per-pair difference walk `D = X_A − X_B` over `{-1,0,+1}`. It does not import the candidate. Agreement is the exact collision probability of two independent winner sets; ties form `{A,B}`. Expected held-out success breaks ties uniformly and uses the frozen known probabilities; it is a model expectation, not observed task data.

## Result

The independent auditor exactly reconstructed the candidate output. All seven frozen gates passed, and all five mutated-result controls were rejected.

| Quantity | High-success regime | Low-success regime |
|---|---:|---:|
| Candidate success probabilities | `(0.9, 0.8)` | `(0.2, 0.1)` |
| Winner-set distribution, `n=1` | A `18/100`, B `8/100`, tie `74/100` | Identical |
| Independent-run agreement, `n=1` | `5864/10000` | Identical |
| All-zero probability at each `n` | `(1/50)^n` | `(18/25)^n` |
| Pooled success probability | `17/20` | `3/20` |
| Expected held-out success, `n=1` | `171/200` | `31/200` |

Across all seven sample sizes, the complete exact winner-set distributions and agreement probabilities matched, while the all-zero, pooled-success and expected held-out quantities differed. Thus the ordinal statistic alone does not distinguish these deliberately symmetric regimes.

The checkpoint binding control preserved action marginals (`A=1/2`, `B=1/2`) while a row permutation changed checkpoint-appropriate outcomes from `2/2` to `0/2`. The stable high-success control remained `7/8`. A correct YIELD remained a typed safe disposition rather than an all-zero candidate tie. A positive but forbidden-effect candidate was refused. For executed-only labels, `N=4`, observed positive `Y=1`, unresolved/missing `M+R=2`; the no-assumption bound was `[1/4, 3/4]`, with no rejected outcome imputed.

## Execution and audit

- Candidate: `python -B candidate.py`, one invocation, exit 0, started `2026-10-01T19:42:32Z`.
- Independent auditor: `python -B auditor.py`, one invocation, exit 0, output `METHOD_PASS_SCOPED`, started `2026-10-01T19:42:39Z`.
- Formal retries, replacements, tuning: zero.
- Environment: Windows host CPU, CPython 3.12.10. No container, model, GUI, network, user data, or live action. The issue requires a disposable finite simulator but not a container; Docker Desktop's service was stopped and the Engine was not responsive in the prior read-only probe.
- Construction record: an initial unittest invocation from the checkout root failed sibling-module discovery; the same five tests passed from the package directory without source changes. This pre-freeze construction event is not the formal result.
- Raw candidate and audit JSON, source blob IDs, SHA-256 values, gates and mutation results are retained in this directory and `RUN.json`.

## Limits

This is exact synthetic method evidence only. It does not measure an actual recovery policy, human choice, GUI task, #59 real-time-control benefit, safety rate, runtime integration, or product readiness. The symmetry result applies to the frozen equal-cost independent Bernoulli construction; checkpoint permutation and typed controls are small authored examples. No historic benchmark result is invalidated, and no unsafe/rejected real action was executed.
