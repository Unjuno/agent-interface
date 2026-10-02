# Historical typed-symmetry preservation qualification

This sidecar accompanies PR #6257 at original head `a72c42fa2133cb2660f37fd8a1962dc1c390ead4`. The 11 original files and their recorded `PASS_METHOD_SCOPED` disposition remain unchanged. This integration preserves the record with the limitations below, not a newly validated full PLAN gate.

## Independent witness coverage

The [frozen auditor](https://github.com/Unjuno/agent-interface/blob/a72c42fa2133cb2660f37fd8a1962dc1c390ead4/research/analysis/symmetry_reduction_6251_t0_host_20261002/audit.py#L250-L290) reconstructs summary fields for all arms but independently replays witnesses only for the symmetric baseline. Mutation-control witnesses are not independently replayed. Baseline checking compares witness count and validates each supplied named trace, without establishing distinct per-class coverage, quotient-key membership or the attached canonical-to-named inverse mapping.

Thus PLAN's independent audit of all witness traces and complete quotient-witness coverage are not established by this auditor. REPORT's every-control expansion claim is candidate-reported. The candidate retains concrete BFS traces from full named-state enumeration and attaches an inverse map; it does not lift a separately explored quotient trace through that map. The recorded 312-to-166 reduction counts classes after full enumeration and is not evidence of reduced exploration cost.

## Provenance annotations

The [preregistration comment](https://github.com/Unjuno/agent-interface/issues/6251#issuecomment-5940479508) records candidate SHA-256 `0390CF0F835D404C6EDD444A223D2D1AFC29029596C683F647CB6F6A10E05672`; FREEZE.json records `0395CF0F835D404C6EDD444A223D2D1AFC29029596C683F647CB6F6A10E05672`. Both are 64 characters and differ by one nibble. The discrepancy is retained, not silently corrected or independently resolved here.

At frozen source commit `926fe2229538702a33cd7379b25ceb7b7bc26a57`, FREEZE.json already contains both before-freeze invocation counters of zero and after-freeze counters of one. Whether the latter are prospective allocation counts or execution counts is ambiguous. Source/manifest Git blob identities are unchanged between that commit and the original PR head; this finding is not evidence of a later frozen-file edit or independent proof of execution chronology.

## Access, checks and scope

The large candidate.raw.json was not fully retrievable through the review connector, so this review makes no full raw-content integrity or witness-coverage validation claim. No candidate, auditor, test, hash recomputation or scientific counterexample was executed. Existing replay CI covers unrelated Doom scheduler tests. The preexisting Analysis Index failure specifically identified this missing directory entry; an additive sorted index entry accompanies preservation.

The retained result concerns an authored finite, host-only model. No real-worker symmetry, hidden actor-state coverage, fairness/liveness, production safety, runtime authority, live interface, external effect, container reproducibility or resolution of the earlier container-readiness HOLD follows.
