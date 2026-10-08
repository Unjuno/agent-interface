# Observation epoch strict join — first outcome

Task `OBSERVATION-EPOCH-STRICT-JOIN-CONTRACT-20260918-001`, Issue #1218, parent #42.

## Decision

**`PASS_OBSERVATION_EPOCH_STRICT_JOIN_SCOPED`**

One source-first deterministic formal invocation, reruns0. No model/provider/network/GUI/X11/task-input/shared-runtime action occurred.

## Frozen factor

The same per-field records were composed under:
- `LATEST_PER_FIELD`: take the latest screenshot/focus/target-binding/authority/effect record independently;
- `STRICT_EPOCH_JOIN`: join only when each requested field appears exactly once, runtime epoch/session/surface match, capture intervals overlap, and target-scoped records share target epoch.

Typed non-success statuses are `PARTIAL`, `STALE`, `SKEWED`, and `UNJOINABLE`. `COHERENT` is observation consistency only; it does not imply readiness, completion or action authority.

## Formal first outcome

300,000 rows = 25,000 ×12 frozen strata.

- candidate/oracle mismatch: 0
- invalid sets emitted COHERENT: 0
- authority promotions: 0
- readiness promotions: 0
- completion promotions: 0
- LATEST_PER_FIELD complete joins on invalid strata: **250,000**
- formal invocation1/reruns0

Invalid strata cover stale focus epoch, stale target epoch, old effect/new screenshot, session mismatch, surface mismatch, same-epoch non-overlapping capture intervals, missing field, conflicting duplicate, identical duplicate, unknown field, and malformed timestamp. Only the fully coherent stratum is admitted.

The baseline count is a deliberate negative discriminator. It shows that selecting each field independently by recency can construct a complete record even when the resulting multimodal snapshot never satisfied the frozen consistency contract.

## Source-first publication integrity

The initial single-file base64 upload differed from the frozen local bundle by one character and was **never authoritative**. It was deleted before result publication.

The authoritative source-first path is the six exact chunk files under `chunks/**`. Remote Git blob identity matched local expectation 6/6 before formal. `CHUNK_MANIFEST.json` fixes the chunk bytes/hashes and reconstructed tar SHA-256 `3422e38eae920c624368bd2a9385e3a39b97994e015133a45e40b06c70e1e8cc`.

## Result integrity

- RESULT SHA-256 `f040f6ec8c0d95a0a36fe4569bcc9ddf6134b74f15aac750b2b5e0900936c6ad`
- AUDIT SHA-256 `20fef1d34892ee4694acea82688d0a6661cf0f311af64fc6ab8f645689a87c81`
- CORRUPTION SHA-256 `7e90ac41a2ae86645f87f316c162e12c3777e12de1bd8a916b21bb241ab79f0b`
- SOURCE_REHASH SHA-256 `ce8faa3fb7670c112adff9c001e6f2739032725b67dbb3f14090ecf8b1a154fe`
- independent audit PASS/errors[]
- copied-result corruptions8/8 reject
- frozen science source rehash6/6 exact

## Boundary

This validates strict multimodal join mechanics only. It does not prove that real screenshot/UI-tree/focus timestamps are correct, that strict exact epochs are optimal, or that a coherent epoch means the application is ready.

The next #42 rung should keep field/epoch semantics fixed and compare strict joining against one preregistered bounded-skew rule on controlled delayed-paint/focus fixtures. Do not change the observation detector and join tolerance simultaneously.
