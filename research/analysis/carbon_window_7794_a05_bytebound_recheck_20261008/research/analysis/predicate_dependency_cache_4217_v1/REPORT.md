# Predicate dependency cache v1 — Result

Issue #4217. Allocation `predicate-cache-4217-20260923-01`.

## Result

**PASS_DEPENDENCY_SCOPED_PREDICATE_CACHE_SCOPED**.

One formal invocation over 13 frozen states × 4 predicates = 52 predicate observations. No reruns, row replacement, exclusion or tuning.

- RECOMPUTE_ALL evaluator calls: 52
- PREDICATE_CACHE evaluator calls: 26
- cache hits: 26
- predicate mismatches versus full recomputation: 0
- graph disposition mismatches: 0
- authority grants: 0
- independent raw-only audit: 145 checks, errors=[]
- copied-evidence corruption controls: 12/12 rejected

Cache miss reasons: COLD 4; DEPENDENCY_GENERATION 5; DEPENDENCY_UNKNOWN 1; INTENT_VERSION 4; PRODUCER_VERSION 4; SOURCE_GENERATION 4; SOURCE_STALE 4. The two unrelated toolbar changes reused all four predicates. Form and target semantic ABA restorations used new dependency generations and therefore recomputed instead of reusing the old values. Intent, producer/model version, stale source, fresh source replacement, last-effect and target controls all invalidated the declared scope as frozen.

Lookup timing is descriptive only: all lookup p50 681 ns, p95 1878 ns; hit p50 485.5 ns; miss p50 862 ns; max 2274 ns on this provided container. No performance promotion gate uses these timings.

## H/T/D/C/U

- H: explicit dependency/version/provenance binding permits narrow semantic predicate reuse without changing predicate or graph semantics.
- T: deterministic standard-library replay in the provided Linux x86_64 execution container / CPython 3.13.5. Four predicates; 13 states covering unrelated mutation, relevant mutation, ABA restoration, intent/model-version changes, UNKNOWN dependency, stale/fresh source generation, last-effect and target changes.
- D: all frozen semantic/invalidation gates pass; evaluator calls fall from 52 to 26; 12/12 corruption controls reject.
- C: deterministic authored evaluator and trace. This is applicability-semantics evidence, not natural GUI distribution or learned-model behavior.
- U: no live authority, cross-session persistence, model/provider, task success, token saving, whole-policy cache, or production integration claim.

## Retained construction/publication incidents

Construction attempt01 failed before formal execution because unittest was launched outside the study directory and could not import `study`. Attempt02 used the same source from its directory and passed 6/6. Both are retained in the preformal freeze.

Before formal execution, GitHub readback caught three publication-only transcription mismatches: the first `environment.json` used values from another execution context, and the initial readable `study.py`/`audit.py` omitted comments present in the locally frozen bytes. No formal row had run. The incorrect commits remain in branch history; exact locally frozen bytes were restored and all 11 frozen Git blob IDs matched before formal authorization.

## Integrity

Formal raw SHA-256: `d0a14107c0f64929ebff012a57191467c35f32af2d83af3e45715b6d2797fa0e`.

The formal raw JSON is retained losslessly as zlib/Base64 with `unpack_formal.py`; first audit, controls, command streams, execution exits, construction failures/success and exact preformal source hashes are retained directly. `verify_publication.py` is read-only and does not rerun the consumed formal allocation.

## Integration meaning

This supports a narrow contract: cached semantic facts should be keyed by their declared dependency generations plus intent, producer/model version and source generation/currentness. Cache validity remains separate from input authority and application-effect admission. A later model-facing or live runtime successor must test whether dependency declarations are complete enough in real tasks.
