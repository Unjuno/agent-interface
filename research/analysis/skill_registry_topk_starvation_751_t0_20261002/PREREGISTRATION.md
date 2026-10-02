# Skill-registry top-k candidate starvation — T0

Allocation: `SKILL-REGISTRY-TOPK-STARVATION-751-T0-20261002-01`  
Parent: Issue [#751](https://github.com/Unjuno/agent-interface/issues/751)  
Prior rung: merged PR #759, `PASS_SKILL_APPLICABILITY_FILTER_SCOPED` (hard-filter semantics only).  
Base main: `afea9a530cafd7af529df4c9e59f36b816bca24f`  
Branch: `research/skill-retrieval-topk-starvation-751-t0-20261002`

## H — hypothesis

With the hard applicability boundary held fixed, semantic top-k followed by applicability filtering can return no candidate even when an eligible skill exists just beyond k. Exact applicability filtering before ranking avoids that false abstention at the cost of scanning the full registry; bounded widening recovers eligible candidates only within its declared scan budget and must report `UNKNOWN_NOT_FOUND_WITHIN_BUDGET` beyond it. None of these methods may select a known hard-incompatible, stale/out-of-envelope, revalidation-required, or unknown candidate.

## T — deterministic finite test

Use eight authored registries with semantic-rank placements at ranks 1, 2, k+1=3, budget edge 6, and beyond-budget rank 7; also include no-eligible and unresolved-UNKNOWN controls. `retrieval_k=2`, `scan_budget=6`. Compare (1) semantic top-k then hard filter, (2) exhaustive hard applicability filter then rank, and (3) semantic-order widening until k eligible candidates or six records have been checked. The hard execution-selection gate is identical in every arm. The oracle is a separate frozen JSON fixture; no model, embedding service, GUI, runtime, network, or external action is involved.

Candidate invocation: exactly one WSLc container, network disabled, pull disabled. Independent raw-only audit: exactly one separate WSLc container, only after candidate exit 0 and complete output. Construction tests and mutation controls run before the formal candidate; no formal retries.

## D — frozen criteria

`METHOD_PASS_SCOPED` requires exact one-to-one accounting of all eight cases and all three methods; no non-`ALLOW` skill selected; exhaustive filtering recovers every known eligible skill; fixed top-k abstains on seeded eligible ranks greater than k without claiming global absence; bounded widening finds every known eligible rank at or before six and returns `UNKNOWN_NOT_FOUND_WITHIN_BUDGET` when the eligible item is beyond six; unresolved eligibility never becomes `NONE_PROVEN_APPLICABLE`; and all frozen auditor corruption controls are rejected. Any unsafe selected candidate is `FAIL_UNSAFE_SELECTION`. Any row/source/oracle mismatch is `STOP_AUDIT`. This is a finite method discriminator only.

## C — competing explanations

A full metadata scan may cost more than widening; a sufficiently large k can reduce the fixed-top-k miss rate but increases presentation cost; applicability metadata may itself be stale or wrong; and a real semantic ranker may not reproduce authored rank order. The experiment holds rank order and truth labels fixed to isolate candidate-generation order.

## U — limits

No embeddings, model selection, tokens, latency, production registry scale, live applicability truth, GUI, action authority, task effect, or safety rate is measured. `NONE_PROVEN_APPLICABLE` is allowed only for a fully scanned registry with no unresolved eligibility. A bounded miss is not evidence of global absence. No runtime promotion follows.
