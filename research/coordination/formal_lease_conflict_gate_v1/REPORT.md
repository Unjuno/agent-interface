# Pre-freeze conflict gate for formal allocations

Task `COORD-LEASE-CONFLICT-GATE-20260916-001`, Issue #346.

Publication BASE: `4e802fa2ec3c0c97545a38520bb18b3b126d8e4e`.
Pre-result freeze commit: `77ec22a41f37dbd7a3c4e6f3689dbef39cab310a`.

**Decision: `PASS_SCOPED_PRE_FREEZE_CONFLICT_GATE`.**

This is a coordination result over a frozen GitHub-visible snapshot. It does not execute a live experiment, grant/revoke input authority, alter shared runtime, or establish an atomic experiment lease.

## Why this experiment exists

The project already retains a real coordination failure: Issue #283's formal allocation was accidentally executed twice, and #307 correctly invalidated the allocation-level promotion as `PREREGISTRATION_VIOLATION_DUPLICATE_FORMAL` rather than selecting the nicer run.

During this intake, independent sessions created several new claims within minutes. Issues #340, #341, #344 and #345 are materially different one-factor questions. Issue #342 independently claimed the same direct Inkscape final-selection question as #341 and was then closed as duplicate. That produced a useful retrospective positive/negative dataset without consuming another live allocation.

## Frozen rule

A proposed allocation conflicts when at least one of these is true:

1. exact `task_id` is already claimed;
2. exact additive write `scope` is already claimed;
3. direct `successor` and curator-authored normalized `question_key` are both equal;
4. `task_id` is already recorded as consumed.

Same application/domain alone is not a conflict. Same predecessor/successor with a different explicit one-factor question alone is not a conflict.

The normalization fields are intentionally authored metadata. This experiment does **not** claim automatic semantic equivalence from arbitrary prose.

## Freeze

Before recording `result.json`, the following Git blob identities were pinned in `prereg.json` and posted to Issue #346:

- `snapshot.json`: `764607fb4b0223f714e168854899a29dcaf31115`
- `audit.py`: `7f07eed689a3aa68beed52c5f0d170e6362a79f6`

The result was absent at freeze.

## First result

### Observed controls

| Control | Frozen expectation | Result |
|---|---|---|
| #341 vs #342 | conflict on same successor + same normalized question | `semantic_successor`, PASS |
| Active #340/#341/#344/#345 | no pairwise conflict | 0 conflicts across 6 pairs, PASS |
| Consumed #283 task identity | reject reuse | `consumed_task_id`, PASS |

### Synthetic controls

| Control | Expected | Result |
|---|---|---|
| duplicate task ID | reject | `task_id`, PASS |
| duplicate additive scope | reject | `scope`, PASS |
| new task/scope but same successor + same question | reject | `semantic_successor`, PASS |
| same domain, distinct successor/question | admit | no reason, PASS |
| same successor, different question | admit | no reason, PASS |
| consumed formal task ID | reject | `consumed_task_id`, PASS |

All six synthetic controls match the predeclared disposition. The four current active experimental claims form six pairs and none is conflated by the frozen rule.

`audit.py` is retained as a deterministic offline reproduction of this table. The result recorded here was derived from the frozen structured snapshot; no CI/interpreter execution is claimed as additional evidence.

## Interpretation

A structured pre-freeze claim record would have been sufficient to catch both kinds of failure represented here:

- a semantically duplicate successor claim with a fresh task ID/scope (#341/#342);
- reuse of an already-consumed formal task identity (#283/#307).

At the same time, the rule does not serialize unrelated current research merely because several experiments use GUI state, concurrency, or freshness concepts.

This is useful, but incomplete. The most important remaining failure is **check-to-claim TOCTOU**: two sessions may both read a conflict-free snapshot before either publishes its claim. A perfect deterministic precheck cannot solve that race by itself.

## H / T / D / C / U

**H — supported at scoped retrospective level.** The structured fields are sufficient for the observed duplicate, consumed-ID control and frozen synthetic matrix.

**T — completed.** One immutable GitHub-visible snapshot, two observed controls, six synthetic controls, no live/model/GUI allocation, first deterministic result retained after source freeze.

**D — PASS.** Observed duplicate detected; active distinct set has zero conflicts; consumed ID rejected; six synthetic controls agree with their frozen expectations.

**C.** The apparent success depends on curator-authored `question_key`. A paraphrased duplicate with a different key can escape; an over-broad key can falsely serialize legitimate ablations.

**U.** GitHub search/index freshness, private/unpushed sessions and simultaneous read-before-create races are unobserved. This is advisory admission checking, not consensus, compare-and-swap, or exactly-once allocation.

## ERROR CHECK

- Historical failure is not relabelled: #283/#307 remains a preregistration violation.
- #342 is used as an observed duplicate control; this report does not claim the new gate caused its closure.
- Active claims #340/#341/#344/#345 remain owned by their existing sessions; this experiment does not execute or mutate them.
- No shared runtime, workflow, model, GUI, X11 or formal measurement allocation is modified.
- No performance, reliability-rate or production-safety claim follows.

## Next single question

Can one canonical GitHub claim record make claim acquisition atomic enough to close the read-before-publish race—for example by serializing ownership through one versioned coordination record—without creating a global research bottleneck?

Do not start that successor until checking whether another coordination session has already claimed it.
