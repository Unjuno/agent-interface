# Invariant-confluence boundary for coordination

Issues #5547 and #8889 ask when invariant-preserving operations can proceed without global coordination. The later #8889 intake found substantial overlap with #5547; its broad discriminator should be consolidated with the existing line rather than run as a duplicate allocation.

## Invariant-confluence contracts — #5547

- **Status:** open; finite synthetic method evidence is scoped, and the general classifier / GUI transfer remains unverified.
- **Source:** [Issue #5547](https://github.com/Unjuno/agent-interface/issues/5547); consumed pre-test STOP preserved in [PR #5558](https://github.com/Unjuno/agent-interface/pull/5558); finite successor in merged [PR #5563](https://github.com/Unjuno/agent-interface/pull/5563).
- **Idea:** Classify coordination need from declared operation effects and hard invariants instead of assuming either universal serialization or universal commutativity. Unknown footprints, hidden effects, and non-transactional external actions remain coordinated.
- **Outcome:** The initial frozen test invocation stopped before any test (`ModuleNotFoundError`); candidate/auditor counts were 0/0, with no retry. Formal-01 later failed because an unlabelled integer quota delta could not preserve replay idempotence while representing distinct concurrent reservations. Fresh formal-02 enumerated 100 finite pairs; 36 were classified monotone-safe with zero modeled invariant violations, while independent conflict witnesses identified refresh-epoch (2), quota reservation (8), and effect commit (20) cases. Five corruption controls were rejected. These results validate only the hand-specified synthetic model; they do not establish a general I-confluence classifier or real GUI safety/coordination savings.

## Overlap correction for #8889

[Issue #8889](https://github.com/Unjuno/agent-interface/issues/8889) initially proposed a similar admission discriminator and its own novelty note later identified #5547 and #5563 as direct prior coverage. It should not get a duplicate broad allocation. Its only possible residual is whether noncommuting-but-invariant-preserving operation pairs create additional safe-concurrency cases beyond #5547's conservative footprint rules; the record itself says this must first be checked against the existing 36 pairs and coordinated with #5547's owner. Until that boundary is established, preserve #8889 as an open overlapping proposal rather than claiming incremental value.

## Safety boundary

The method concerns admission policy over a finite transition model. It does not make external GUI effects atomic, observable, reversible, or safe to merge. Freshness, authority, release, and effect receipts remain independent hard gates; no runtime change or parallel real action follows from these results.
