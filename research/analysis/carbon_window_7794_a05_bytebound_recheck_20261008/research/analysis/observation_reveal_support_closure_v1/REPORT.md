# #1820 REVEAL support-closure composition — retained formal result

Task: `OBSERVATION-GATING-O3-REVEAL-SUPPORT-CLOSURE-20260919-001`

Decision: **`PASS_O3_REVEAL_SUPPORT_CLOSURE_SCOPED`**.

## Question

#689 retained `REVEAL(target)` feedback mechanics in which a unique current target may return a target-context crop, while absent/duplicate target evidence falls back to exact-current RAW. #1726 separately established that a current relevance declaration is not necessarily complete.

This composition asks what evidence support is actually required to reuse the model-visible crop safely.

The crop bytes alone are not enough because `CONTEXT_READY` depends on the target remaining globally unique. A second matching target can appear outside the crop while the crop itself remains byte-identical.

## Analytical witness

Two current-source worlds expose the same target crop:

- W0: one outside tile changes only irrelevant decoration. `CONTEXT_READY` remains valid, so crop reuse is allowed.
- W1: one outside tile becomes another matching target. Global uniqueness is false, so #689 requires `RAW_FALLBACK`.

A crop-only gate receives identical crop evidence but must produce different safe decisions. Therefore presentation support and branch-validity support are different.

For this global-unique `REVEAL(target)` contract, the branch-support closure includes the global uniqueness/ambiguity predicate. That predicate may be evaluated locally on full current evidence without forwarding the full image to the model.

## Candidate

- `CROP_ONLY`: current unchanged crop => `REUSE_CONTEXT`.
- `CROP_PLUS_GLOBAL_UNIQUENESS`: reuse only if exact-current local verification proves one matching target and it is the crop target; duplicate target => `RAW_FALLBACK`.

Existing #689 boundaries remain fixed: stale source rejects, critical events bypass presentation, changed/removed target crop falls back, and unbound uniqueness evidence is rejected.

## Construction

Directed construction: `PASS_CONSTRUCTION_ELIGIBLE`.

- irrelevant outside change -> candidate `REUSE_CONTEXT`;
- duplicate outside target -> baseline `REUSE_CONTEXT`, candidate `RAW_FALLBACK / AMBIGUOUS_TARGET`;
- critical -> forward;
- stale source -> reject;
- target removed/changed -> raw fallback;
- unbound uniqueness evidence -> reject;
- malformed count/state/binding -> 3/3 reject.

Source/PLAN/manifest Git blobs read back exactly. Construction summary bytes were normalized before freeze; scientific source was unchanged.

## Frozen formal

Exactly one exhaustive invocation; reruns/replacements/tuning `0/0/0`.

Source model:
- two fixed crop tiles;
- ten outside tiles;
- each outside tile independently in `{UNCHANGED, IRRELEVANT_CHANGE, DUPLICATE_TARGET}`;
- all `3^10 = 59,049` outside configurations;
- crossed with critical-event flag and source-current flag.

Total: **236,196 rows**.

| Metric | Result |
|---|---:|
| CROP_ONLY false suppressions/reuses | **58,025** |
| CROP_ONLY safe reuses | 1,024 |
| support-closure candidate false suppressions | **0** |
| candidate safe crop reuses | **1,024** |
| candidate ambiguity/raw fallbacks | **58,025** |
| candidate critical forwards with current source | 59,049 |
| candidate stale-source fallbacks | 118,098 |

The exact combinatorial discriminator is:

- configurations with no duplicate target: `2^10 = 1,024`;
- configurations with at least one duplicate: `3^10 - 2^10 = 58,025`.

The candidate preserves every safe crop reuse while eliminating every frozen crop-only ambiguity escape.

## Integrity

Independent audit derives the counts without importing candidate policy. Decision: `PASS_O3_REVEAL_SUPPORT_CLOSURE_SCOPED`; errors `[]`; corruption controls 7/7 reject.

- formal result SHA-256: `6141bbb3537bcf98d2af8ff7df7f85e078544b90207cc4b7a419c4de243062a7`;
- audit SHA-256: `ad86a64e97f457c1d53af7da536873c6fd8ac8ddbe88e2fec019a6d5a1c4ffad`;
- deterministic ledger SHA-256: `4b67c2b9195d0ff6b86cdbf395e06af84607409fec505193ab647ce768e0f155`.

Postformal source hashes match the frozen source exactly.

## Interpretation

A narrow model-facing presentation does not imply that every local branch-validity predicate has narrow evidence support.

For the frozen global-unique REVEAL contract:

`model presentation support = target crop`

while

`local branch-validity support = target crop + global uniqueness evidence`.

This role separation permits crop reuse without silently hiding ambiguity. It does **not** reduce full-current capture or local verification cost; it only establishes when full-current evidence need not cross the model boundary.

A trusted complete target index, accessibility source, or semantic object table could satisfy the global uniqueness support without pixel-wide scanning. Conversely, an instruction whose semantics are explicitly ROI-local would not require this global closure.

## Boundary

Synthetic contract-composition semantics only. No real target-detector accuracy, GUI frequency, capture/compute savings, model quality, token saving, latency, or production ABI claim. #1635 and O4 remain independently owned.
