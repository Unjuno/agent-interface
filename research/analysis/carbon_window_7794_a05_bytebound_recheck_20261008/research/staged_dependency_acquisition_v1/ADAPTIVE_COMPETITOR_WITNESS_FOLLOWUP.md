# Follow-up — adaptive false-witness fast path for branch uniqueness

Status: **RETAIN as a semantic evaluation candidate for branch sets without a mutual-exclusion certificate; no physical speed claim.**

## Question

The general correctness rule is to preserve the same unique branch-selection result. Full recomputation can require predicates from every competing branch. Can an uncertified branch set revalidate uniqueness more cheaply without freezing a broad inactive-branch union?

At plan time every non-selected competitor is false. Therefore each competitor has at least one condition that does not match the plan observation. Retain one such condition as a **false witness**.

At final admission:

1. revalidate the selected branch completely;
2. check the retained false witness for each competitor;
3. if the witness still mismatches that competitor, the competitor is still false and no other condition from it is needed;
4. if the witness now matches, evaluate that competitor fully; reject only if it now matches.

This is a short-circuit implementation of full branch matching, not a weaker validity rule.

## Generated experiment

100,000 seeded attempts generated 2–4 v1-style conjunction branches over five ternary predicates. 195 branch sets had no observation with exactly one matching branch and were excluded before mutation, leaving **99,805 scored trials**.

For each scored trial, the current observation kept each plan-time predicate value with probability 0.8; otherwise that predicate changed to one of the other two values. This mutation model is a fixture choice, not a natural-workload claim.

Compared:

- `selected_only`: revalidate only the selected branch;
- `frozen_witness`: selected branch + one stored false witness per competitor; if a witness stops blocking, reject immediately;
- `adaptive_witness`: selected branch + witnesses, but fully reevaluate only competitors whose witness stopped blocking;
- `full_union` is used only as a distinct-predicate-count reference.

| method | stale accepts | false rejects | mean distinct predicates | median |
|---|---:|---:|---:|---:|
| selected only | **2,956** | 0 | 1.929 | 2 |
| frozen witness | 0 | **4,850** | 2.654 | 3 |
| **adaptive witness** | **0** | **0** | **2.718** | **3** |
| full branch-union reference | — | — | 4.303 | 5 |

## Why adaptive witness is exact

Assume all final reads refer to the same authoritative final decision boundary.

- The selected branch is revalidated completely, so it matches iff the selected-side test passes.
- Every competitor whose retained witness still mismatches is definitely false.
- Every competitor whose witness no longer mismatches is evaluated completely, so its final truth is known exactly.

Therefore the algorithm accepts iff the selected branch matches and every competitor is false, which is exactly the unique-selection predicate.

The frozen-witness variant is sound but incomplete: a chosen witness can stop blocking while another condition still keeps the competitor false, creating the 4,850 observed false rejects.

## Adversarial witness invalidation

A second block targets the fast path directly. For each generated unique-plan case, every retained witness is changed to the value expected by its competitor. Cases are scored only when those witness changes can be applied consistently and the originally selected branch still matches, so the block isolates competitor handling rather than selected-side failure.

From 100,000 attempts, **39,469** cases satisfied those scoring conditions.

| method | stale accepts | false rejects |
|---|---:|---:|
| selected only | **18,259** | 0 |
| frozen witness | 0 | **21,210** |
| **adaptive witness** | **0** | **0** |

Adaptive evaluation checked mean **3.640** distinct predicates versus full-union mean **4.159** in this adversarial subset and fully reevaluated a median of one competitor. Logical predicate count is not a latency claim.

This block demonstrates the intended degradation path: when every retained witness is deliberately invalidated, the algorithm falls back to exact competitor evaluation rather than turning a fast-path miss into either stale execution or immediate false rejection.

## Architecture consequence

The semantic token remains:

`BRANCH_SELECTION(state, selected_branch, unique=true)`.

Three implementation tiers are now available:

1. **static mutual-exclusion certificate** — for v1 states whose competitors are provably exclusive, revalidate only selected `when`;
2. **adaptive false-witness path** — for uncertified branch sets, check plan-time false witnesses and expand only competitors whose witness no longer blocks;
3. **full recomputation** — correctness fallback.

These tiers must produce the same semantic branch-selection verdict. Backend batching/latency is a separate question.

## H / T / D / C / U

**H.** Plan-time false witnesses can short-circuit exact branch-selection revalidation without introducing stale accepts or frozen-witness false stops.

**T.** Primary block: 100,000 attempts / 99,805 scored unique-plan cases under one fixed mutation model. Adversarial block: 100,000 attempts / 39,469 scored cases where all retained witnesses are deliberately invalidated while the selected branch remains true.

**D.** RETAIN adaptive witness: 99,805/99,805 correct in the primary block and 39,469/39,469 correct under targeted witness invalidation. FAIL selected-only as incomplete. HOLD frozen witness as overly conservative. Distinct predicate counts are semantic-acquisition counts only.

**C.** A different witness-selection policy could reduce checks further; conversely, physical acquisition may be batched such that fewer logical predicates do not reduce latency. Witness and fallback reads must belong to one coherent final-admission state or be protected by equivalent version/transaction semantics.

**U.** Generated known-ground-truth branches; no exact runtime execution; no network/GUI producer; mutation distributions synthetic; no solver or cost-aware witness choice.

## Next smallest experiment

Do not optimize witness selection yet. The next correctness question is **coherence**: can witness checks and fallback competitor reads observe a fractured state if they are acquired at different times? Test sequential versus snapshot/transactional final-admission reads before any runtime integration of the fast path.
