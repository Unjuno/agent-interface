# Issue #6498 T0 result

Disposition: `METHOD_PASS_SCOPED` for the eight-row synthetic predicate-boundary assay.

## Execution

- Host Python 3.11.9, standard library only. Construction test passed 1/1.
- Candidate ran once and emitted eight ordered computation rows; the candidate saw only `fixture.json`.
- A separate auditor ran once against `raw_candidate.json` and the separate `oracle.json`; it independently reconstructed all eight results, reported zero errors, and rejected all nine predeclared mutations.
- No container, WSLc, external service, cryptographic library/proof system, private data, model, GPU/CUDA, real GUI, or task effect was used.

## Boundary findings

- Exact-target/effect/receipt predicate: the synthetic computation can return true. Classification is only `COMPUTATION_TRUE_PREDICATE_ONLY`; no capture-origin or task-effect claim follows.
- Wrong target: computation is false.
- Correct target event with omitted collateral: `COVERAGE_UNPROVEN`.
- Commitment timestamp after outcome: `PREOUTCOME_COMMITMENT_UNPROVEN`.
- Stale capture: `FRESHNESS_UNPROVEN`.
- Scorer version mismatch: `SCORER_BINDING_FAILURE`.
- False-origin claim: `ORIGIN_UNPROVEN`.
- A valid computation for a visibility-only predicate: `PREDICATE_INSUFFICIENT` for the intended effect.

All eight oracle rows retain `task_effect_claim = NOT_ESTABLISHED_BY_T0`; candidate rows cannot claim whole-task success. The nine rejected controls were score flip, evidence digest substitution, post-outcome time rewrite, scorer swap, whole-task overclaim, coverage promotion, stale-age erasure, forged origin claim, and predicate upgrade.

## Limits

This is finite synthetic method evidence only. The SHA-256 field is a local digest/checksum, **not** a cryptographic commitment, proof, or origin authenticator. No cryptographic soundness/zero-knowledge, proof-system cost, privacy, capture authenticity, GUI correctness, effect, deployment or generalized security claim is supported. A private raw auditor may be cheaper and more semantically capable. This T0 does not authorize T1.

## Provenance

- Freeze: `FREEZE.json` (main observed at intake: `b77e894138afaacbc6eb43cb08bc12873e276f67`). The experiment is self-contained and does not test current repository runtime code.
- Candidate raw SHA-256: `fab07a6a53e3f1b45dbde2cae8b72838fad8e4f7a1f43b7a2a949beffbc7f4f1`.
- Audit JSON SHA-256: `fb989e463a988832765ef3053996bc138ccbb60080902fe7c0e4a818cdf63e86`.
- Main observed at result checkpoint: `cd651d32e772f03e7d60d7787cdfee3ecc57048a`.
