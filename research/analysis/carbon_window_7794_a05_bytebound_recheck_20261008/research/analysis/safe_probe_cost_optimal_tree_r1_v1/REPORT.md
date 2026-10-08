# Safe-probe cumulative-cost optimal tree R1 — retained result

Issue #1874. Parent #1716. Direct predecessor #1836.

## Disposition

**PASS_SAFE_PROBE_COST_OPTIMAL_TREE_SCOPED**

Formal1 / reruns0 / replacements0 / tuning0.

## Analytical result

For a remaining deterministic hypothesis set `V`, positive-cost explicitly safe probes, and a no-prior worst-case objective:

[
C(V)=0quad	ext{if }|V|le1
]

and otherwise

[
C(V)=min_{pin P_{safe},,p	ext{ discriminates }V}
left[c_p+max_o C(V_{p,o})ight],
]

with `IMPOSSIBLE` if no finite safe separating tree exists.

### Why the recurrence is exact

Any valid decision tree has some first safe probe `p`. That probe incurs `c_p`. With no trusted prior, the worst case may realize any nonempty output cell `V_{p,o}`; the remaining subtree must solve the same identification problem on that cell. Replacing any subtree by a cheaper valid subtree cannot hurt the rest of the tree. Induction on `|V|` therefore gives the Bellman optimum.

Positive probe costs imply a nondiscriminating probe is never useful: it pays cost without shrinking `V`.

Safety is lexical: unsafe probes are removed before cost/information optimization.

## Formal verification

Exhaustive universe:
- hypotheses2..4;
- exactly2 binary probes;
- all output maps;
- all safe-flag combinations;
- costs1..3;
- total **12,096** instances.

Random corpus:
- **100,000** deterministic instances;
- hypotheses2..9;
- probes2..7;
- output alphabets1..4;
- costs1..9.

Results:
- candidate/oracle mismatch: **0**
- IMPOSSIBLE mismatch: **0**
- unsafe selected: **0**
- label-permutation decision changes: **0**
- empty-safe cases: **2,000**, all fail closed
- #1836-style one-step greedy cumulative-cost suboptimal cases: **8,977**

Directed discriminator:
- one safe perfect probe cost10;
- two safe orthogonal binary probes cost1 each;
- one-step minimax residual chooses the perfect probe and pays **10**;
- optimal decision tree uses the two cheap probes and has worst-case cumulative cost **2**.

A perfect unsafe cost0 probe is ignored. A nonseparating safe family returns `IMPOSSIBLE`.

Primary audit passes five corruption controls. Independent audit uses a separate frozenset decision-tree implementation and regenerates the random corpus; errors[].

## Preformal execution-transport stop

An attempted interactive/session container dispatch was rejected by the container layer with `StreamingExecNotEnabledContainerError` before Python launched. No result file existed and formal invocation remained0. The frozen source/corpus/gates were unchanged. The subsequent ordinary non-streaming command is the single scientific formal invocation.

## Scope

This establishes deterministic finite-horizon decision-tree semantics for positive additive probe costs under a worst-case/no-prior objective.

It does not cover stochastic outputs, state-changing probes, reversibility, semantic safety classification, posterior priors, approximate identification, real GUI actions, latency distributions or runtime ABI.

## Next legal rung

Either transfer the selector to an observation-only capability/focus-query fixture, or define a distinct stochastic/prior-weighted objective. Do not let probe informativeness override the safe envelope.
