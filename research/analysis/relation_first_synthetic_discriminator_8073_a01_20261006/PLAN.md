# #8073 synthetic discriminator rung

H: On a frozen corpus containing low-lexical/high-relational positives and high-lexical/low-relational decoys, relation-field retrieval should recover all seeded positives while keyword overlap should preferentially surface the decoys.

T: Eight target cards, 24 source cards, top-3 retrieval. Compare exact Jaccard over frozen keyword tokens vs exact Jaccard over frozen relation-edge strings. One candidate invocation, one independent auditor invocation, then ten copied-output corruption controls. No external search/model/GUI/network.

D: PASS_SYNTHETIC_RETRIEVAL_DISCRIMINATOR_SCOPED only if relation-first retrieves all 8 seeded positives, keyword-first retrieves 0 seeded low-lex/high-rel positives, relation-first valid yield exceeds keyword-first, relation-first decoy count is lower, authority=false, independent audit has zero errors, and 10/10 controls reject.

C: This corpus is intentionally constructed to contain the hypothesized discriminator. It validates pipeline sensitivity, not real literature-search superiority. It does not measure query effort, reviewer agreement, or source validity beyond authored labels.

U: Real search-engine ranking, external literature coverage, target selection, reviewer expertise, actual idea quality, testability, and productivity remain untested. The full #8073 T0 still requires frozen external corpus and blinded assessment.
