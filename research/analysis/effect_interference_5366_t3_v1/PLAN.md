# Issue #5366 T3 — resource-envelope freshness

## H/T/D/C/U

- **H:** A resource-interference bound learned under a prior load generation can admit a read that misses a controller deadline after shared-resource load changes. Binding the envelope to the current generation should fail closed as `UNKNOWN` after that change while preserving a current under-budget read.
- **T:** Four deterministic synthetic observations share one serialized server: current low-cost, stale old low bound, current over-budget, and current unknown. Each read starts at t=-1 ms; a 1 ms controller arrives at t=0 with a 2 ms deadline. Compare semantic-only, bound-only, and generation-bound resource gates (12 rows).
- **D:** `PASS_METHOD_SCOPED` only if an independent raw-only auditor reconstructs all rows; generation-aware policy admits current low-cost, leaves stale/unknown non-authoritative, denies current over-budget, has zero late completions, preserves semantic/resource separation, and rejects all four construction mutations.
- **C:** Runtime serialization or fresh measurement may dominate manifests; conservative UNKNOWN on load changes may sacrifice useful observations. A robust online measurement could be better than generation invalidation.
- **U:** Fixture values are synthetic. No actual X11/AT-SPI service-time or generation measurements, runtime, GUI, model, task effect, safety, or product claim.

Formal allocation: `EFFECT-INTERFERENCE-5366-T3-20261002-01`; exact pre-run hashes live in `FREEZE.json`. Candidate and auditor may each run once; retries=0.

## Frozen queue rule

For an admitted read of actual duration `d`, controller completion is `max(0, d - 1) + 1` ms. For a refused read it is 1 ms. A completion is late iff greater than 2 ms. Admission may inspect semantic effect, declared bound and (for the generation-bound arm) equality between envelope and current generation. `actual_service_ms` is oracle-only scoring data.
