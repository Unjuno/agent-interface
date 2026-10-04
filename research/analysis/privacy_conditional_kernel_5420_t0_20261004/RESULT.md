# Issue #5420 conditional-kernel admission gate — T0 result

**Disposition: `PASS_METHOD_SCOPED`.** The frozen finite fixture demonstrates that a marginal-only comparator accepts the shared-pad pair even though conditioning the second release on the same recipient's prior observation yields disjoint output supports across neighboring secrets. The conditional-kernel gate rejects that pair and accepts both the fresh-independent-pad and constant-output controls.

## Evidence

- Preregistered H/T/D/C/U, exact channels, and limitations: [`src/PLAN.md`](src/PLAN.md).
- Frozen protocol and source hashes: [`raw/freeze.json`](raw/freeze.json); freeze SHA-256 `23ec62ce748e7d446d46a851d88121f9e861ff55f92c419a41349646d0a9abd7`.
- Candidate raw: [`raw/candidate.jsonl`](raw/candidate.jsonl), SHA-256 `a93758c7a4cc00ef8f56b7aad7b16e5e58791a110d2671faf8b1dc51ec941cad`.
- Independent raw-only audit: [`raw/audit.json`](raw/audit.json), SHA-256 `c331e85d30fa80cad552af21d882e9a5f7e7fc0e353b9cd9082b4fe61667a570`.
- Exact commands, observed exits/stdout, invocation counts, and no-retry record: [`raw/execution_receipts.json`](raw/execution_receipts.json).

The candidate and independent auditor each ran once in the pinned, network-disabled OrbStack container. The auditor reconstructed 16 rows across three scenarios, reported zero errors, and rejected all four preregistered corruptions. Independent inspection confirms the shared-pad conditional support is secret-disjoint; fresh-pad conditional output is uniform under both secrets, and the constant control always returns zero.

## Interpretation and limits

This supports the method-level claim for these exact finite binary channels only. It does not establish an ε-DP guarantee for an arbitrary interface or deployed product, and it measures no actual UI, timing, consent, multi-recipient, or provider-knowledge behavior. Conditional Shannon information is not ε-DP. This is a successor refinement of the conditional-kernel idea in #5420, not a rerun of merged T1 PR #5445.

Formal invocations are complete; no retry is authorized by this record. Repository/index CI and review are separate integration gates.
