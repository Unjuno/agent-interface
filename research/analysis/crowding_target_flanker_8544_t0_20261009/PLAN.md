# Issue #8544 T0 A01 — target–flanker endpoint scorer method check

## Scope

This is the Issue's no-model T0 measurement-method check, based on current `main` `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`. It does not test the H claim about any VLM and cannot establish crowding-like behavior. T1 requires separate owner/resource review and a fresh allocation. Authority is `NONE`.

## H / T / D / C / U

**H.** A preregistered scorer can distinguish correct target binding, neighbor substitution, miss, abstention, schema error, ambiguous identity, correct rejection, and false alarm while preserving detection separately from identity binding. A fully crossed synthetic layout ledger can keep spacing, image-space eccentricity proxy, target size, flanker condition, placement, and presence balanced across disjoint development/held-out seeds with global control count fixed.

**T0.** Build a deterministic, no-model fixture with 5,632 planted response cases over target presence (present/absent), spacing (24/72 px), image-space eccentricity proxy (120/360 px), target size (24/48 px), flanker condition (near duplicate/dissimilar/text-distinct/no flanker), placement (inward/outward), eight layout seeds and endpoint templates. Six seeds are development and two held out. The raw-only auditor reconstructs exact fixture IDs and denominators, scores response schema/identity/point against independently frozen target and neighbor rectangles, checks paired seed support and split isolation, verifies complete factor crossing at constant global control count, and applies six mutation controls. This is a scorer/fixture test; endpoint labels are planted and do not estimate a spacing effect or predictor performance.

**D.** `PASS_METHOD_SCOPED` only if all 5,632 fixture cases are present exactly once; all eight endpoint classes are classified as planted; wrong-neighbor binding remains distinct from miss while both retain detection status; target-absent correct rejection and false alarm remain distinct; held-out seeds do not overlap development; each factor stratum has all eight seeds; global control count is four in every cell; the full factorial is balanced; and six mutations for row loss, split leakage, density alias, wrong identity, wrong presence and authority inflation are rejected. Any mismatch is `FAIL_METHOD`; output/audit contract errors are retained as STOP/HOLD with no retry. One candidate and one auditor invocation, retries zero.

**C.** This checks scorer behavior on planted JSON outputs only. It does not validate an image renderer, natural-language prompt, real oracle annotation, or the endpoint's stability on model responses. Global item count is controlled, while local geometry and the declared flanker condition are intentionally varied.

**U.** No model call, image-based judgment, human participant, GUI actuation, or empirical predictor comparison occurs. The result cannot support a transfer signal, null transfer finding, human equivalence, cross-model generalization, real-app safety, or runtime adaptation. It is CPU-only stdlib work with no network, external effect, user data, or container semantics.

## Construction and frozen invocation

The construction suite has five tests; formal outputs must be absent before freeze. Candidate and auditor commands are fixed in `FREEZE.json`. Commit and push the freeze, preregister its commit and hashes on Issue #8544, and verify remote readback before either formal invocation. Run candidate once; only if it exits zero and its output hash is retained, run the independent auditor once. No retries or post-freeze edits.
