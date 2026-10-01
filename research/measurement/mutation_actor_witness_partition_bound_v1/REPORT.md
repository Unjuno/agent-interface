# #1600 trusted-witness partition lower bound

Decision: **PASS_ACTOR_WITNESS_PARTITION_BOUND_SCOPED**.

## Result

The predecessor #1579 proves that actor-free event/effect/timing/focus/state observations cannot distinguish hidden producers when verifier-visible inputs are identical. This successor generalizes that boundary: the finest actor taxonomy that can be safely claimed is bounded by the equivalence classes induced by an independent trusted witness.

For the five hidden actor classes `THIS_INTENT`, `THIS_SESSION_OTHER_INTENT`, `EXTERNAL_PROCESS`, `HUMAN`, and `OS`, all 52 set partitions were enumerated as possible witness partitions and all 52 as requested actor taxonomies. Across all **2,704** witness/taxonomy pairs, an independent operational classifier-feasibility check agreed with the analytical partition-refinement criterion in every case. Feasible pairs: **358**; refinement mismatches: **0**.

Selected ABI rungs:

- **NONE** — 1 witness state; only 1 safe taxonomy; exact five-class attribution is impossible.
- **SELF_BIT** — 2 witness states (`THIS_INTENT` vs all non-self); 2 safe taxonomies; exact five-class attribution is impossible.
- **SESSION_SCOPE** — 3 witness states (`THIS_INTENT`, same-session other intent, coarse external); 5 safe taxonomies; exact five-class attribution is impossible.
- **EXACT_ACTOR_CLASS** — 5 singleton witness states; all 52 taxonomies are safely representable, including exact five-class attribution.

Therefore exact identification of all five declared classes needs at least **five distinguishable trusted witness states**. A fixed-length binary encoding needs at least **three bits** because two bits encode at most four states. This is a cardinality lower bound only: enough bits do not make an unauthenticated, stale, cross-scope, or forgeable field into trusted provenance.

## Proof boundary

`PROOF.md` establishes necessity and sufficiency: exact deterministic classification into a requested taxonomy is possible iff each witness equivalence cell lies wholly within one requested taxonomy cell. Equivalently, the witness partition must refine the requested taxonomy.

This means actor taxonomy design should start from the evidence actually available. A one-bit self/nonself witness justifies a coarse self/nonself distinction; it does not justify claiming HUMAN, OS, or EXTERNAL_PROCESS specifically. More model capacity cannot recover distinctions erased by the witness equivalence relation.

## Verification

- formal analytical/exhaustive invocation: 1
- reruns/replacements/tuning: 0
- set partitions: 52
- witness/taxonomy pairs: 2,704
- refinement/operational mismatches: 0
- exact-five-class minimum witness states: 5
- fixed-length encoding lower bound: 3 bits
- frozen audit: PASS
- independent RGS-based audit: PASS
- corruption controls: 7/7 rejected
- authority promotions: 0
- task-success promotions: 0

Parent #1579 blobs are pinned exactly:
- REPORT.md `a5ef28df339642cde2d585fcc199197635a1da25`
- RESULT.json `8ff6b368329d05e7724330305ff8cd006401aa42`
- PROOF.md `9bf2190fab6429b2a98900c20fcf438e7f822efd`

## Retained packaging failure

After the successful formal and independent audit, the first packaging command used `sha256sum "$W"/*`, which also matched `__pycache__` and returned exit 1. No scientific command was rerun. `PACKAGING_FAILURE.json` records this postformal failure; the repair hashes regular files only.

## Scope / next discriminator

This is an identifiability/contract lower bound, not proof that any real provenance source is trustworthy or appropriate. A next live successor should test one concrete independent witness source—such as an authenticated input broker or OS/kernel-scoped provenance—and measure authenticity, scope binding, replay resistance, privacy exposure, availability, and overhead. Do not infer HUMAN/process identity from timing or pixels when the witness does not distinguish them.
