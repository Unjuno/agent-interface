# Issue #6498 T0 — pre-registration

## H / T / D / C / U

- **H:** A tiny deterministic predicate can return the correct computation result while still failing to establish capture origin, pre-outcome commitment, freshness, full effect coverage, or whole-task success. T0 tests whether those boundaries stay separate in a finite synthetic method assay.
- **T:** Eight non-sensitive synthetic “GUI evidence” cases, frozen before execution, with a separate oracle. Candidate computes a deterministic Boolean for either an exact target/effect/receipt predicate or an intentionally insufficient visibility-only predicate. Independent auditor reconstructs the computation from frozen bytes and labels wrong target, omitted collateral, after-outcome commitment, stale capture, scorer-version mismatch, false-origin claim and valid-but-insufficient predicate separately. The digest is an integrity checksum only—not a cryptographic commitment or proof. No proof system, GUI, model, private data, or container is used.
- **D:** `METHOD_PASS_SCOPED` only if all eight statements are independently recomputed, all oracle boundary labels match, no candidate row promotes a statement to task success, and all nine frozen mutations are rejected: score flip, evidence-digest substitution, post-outcome time rewrite, scorer swap, whole-task overclaim, coverage promotion, stale-age erasure, forged origin claim and predicate upgrade. Otherwise `METHOD_FAIL`; no retries.
- **C:** A private auditor with raw access may be simpler and semantically stronger. A fixed predicate can correctly attest only its bounded computation; it cannot prove the input's real origin, scope completeness, freshness, causality or GUI effect.
- **U:** One authored finite synthetic fixture. No cryptographic soundness/zero-knowledge, capture authenticity, real GUI/effect, privacy compliance, proof-system cost, deployment, or generalization claim. T1 requires separate tooling, security, privacy, resource and independent-verifier review.

## Frozen execution

- Candidate sees `fixture.json` only. `oracle.json` is separate and used only by the independent auditor. The host CPU runner uses Python standard library only.
- Candidate: `python candidate.py --fixture fixture.json --output raw_candidate.json` — one formal invocation.
- Auditor, only after candidate exit 0: `python audit.py --fixture fixture.json --oracle oracle.json --raw raw_candidate.json --freeze FREEZE.json --output audit.json` — one separate invocation.
- Construction test suite is distinct from those two formal invocations. No retry, replacement fixture, model/GPU/CUDA, container, external proof service, private data, real GUI or task effect.
- The fixture's `origin_attested` is merely a synthetic claim bit and is not authenticated. Even the positive exact-predicate case is classified `COMPUTATION_TRUE_PREDICATE_ONLY`; origin/effect are not established.
