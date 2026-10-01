# Archival qualification for the #4193 v3 publication

Date: 2026-10-01. Reviewed publication: [PR #5389](https://github.com/Unjuno/agent-interface/pull/5389), exact head `68f75c7ef045cf46168ef89801b55a63a6b077a4`.

## Archival disposition and authority

**Archive the published v3 files as historical source and publication evidence only. The published machine result is invalid JSON. This is not acceptance of a reproducible v3 result or a current artifact-level AUDIT_PASS.**

This additive qualification leaves all six published v3 files byte-for-byte unchanged, including the malformed `RESULT.json`. The retained #4193 original source and first allocation outcome remain unchanged. The historical disposition is `HOLD_ATTACK_TASK_EFFECT_NOT_REPRODUCED`; v3's reported retained-source interpretation is `HOLD_NO_POSITIVE_SCORER_EVENT`. Neither becomes a construction, live task-effect, recovery, or causal-efficacy PASS through archival integration.

The static review used published file bytes, Git object hashing, JSON syntax checking, source reading, and decoding/inspection of the existing retained raw data. It did not import or execute any experiment runner, auditor, test suite, or research program. No original output was regenerated, repaired, normalized, replaced, or used to open a new allocation.

## Verified publication gap

The exact published [RESULT.json](RESULT.json) is 1,923 bytes:

- Git blob SHA-1: `68fc2506ea4c52ff343fa2e9cc4e40a2c910df45`
- SHA-256: `6f6188814bbbb5aea6bd791a096c1938c2a920da9a0f993d27b491bcb6bcdaf7`
- The computed Git blob identity agrees with the published GitHub object
- Strict UTF-8 decoding succeeds
- Standard JSON parsing fails with `JSONDecodeError: Invalid control character at: line 10 column 55 (char 416)`
- The failing character is at zero-based byte offset 425 and is byte `0x1e`

The record starts with readable summary fields but becomes corrupted inside the `noinput_sessions_with_positive_scorer_endpoint` key. Readable prefixes and reported console output do not provide a valid substitute for the complete machine artifact.

[REPORT.md](REPORT.md) calls this file the canonical machine record. [VERIFY.md](VERIFY.md) preserves a historical account of runner/auditor exit 0 and says that publication artifacts were verified. Those are historical execution/publication claims; they do not establish validity of the exact published malformed blob. Source inspection shows `audit.py` reads the supplied result with `json.loads`, so this published file cannot reach that auditor's normal checks without first resolving its parse failure. No auditor invocation was performed in this review.

**Do not repair this blob in place or present a reconstructed JSON document as the original result.** Any future correction must be separately authorized and additive, preserving this publication and its identity.

## Retained source facts, separately scoped

The dependency is the existing [#4193 RAW_USED.json.xz](../../map01_v12_attack_task_effect_live_v1/RAW_USED.json.xz). Its bytes were read independently of the malformed v3 result:

- Size: 7,392 compressed bytes
- Git blob SHA-1: `4d1724ba270870d01ca3316843c32116b0aa74a6`
- SHA-256: `0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740`
- The calculated Git blob and SHA-256 both match the published dependency
- The same dependency blob is present at v3 intake `8265c1a19cbba7ab0f5316f27bdb59509269399d`, the PR's merge-base snapshot `e81cbac968752791678d22a4de3f2d276497d614`, and inspected main snapshot `1eec6a58a817b67cd09f2df0e7ab0669b8229462`

Bounded static inspection of the decoded retained data establishes:

- Exactly six named sessions: `p1/p2/p3-attack` and `p1/p2/p3-noinput`
- Sample counts 32+32, 34+32, and 32+32, totaling 194
- Every inspected scorer payload identifies `independent-progress-sample-v2`; sample timestamps are integer values and strictly increase within each session
- All retained sample `kill_count` values are 0 and all `map_exit` values are false, so these retained samples show no positive endpoint in either arm
- Each attack session has one input admission and one input release; their confirmed native DOWN/UP bracket and adapter records agree on owner, intent, key, actuation identity, and the corresponding intervals, with nonempty press/release identities
- No-input sessions contain no input-admission or input-release event
- The decoded retained event/sample records contain neither `source_event_id` nor `scorer_event_id`

These observations corroborate the limited retained-source HOLD interpretation. They do not validate the malformed machine result, certify the original measurement beyond retained evidence, or reproduce an experiment. They do not establish a general multi-actuation plan/receipt join, application consumption, new scorer provenance, live task effect, or recovery efficacy.

## Source-validation limits

The published v3 runner and auditor match the source blobs at the verification record's cited code snapshot `fd206cb1cd0ff4948835afa7b9e9b4f120e032e4`. They are preserved source, not promoted to a general evidence validator.

In particular, their `contains_key` helper traverses dictionaries and lists but does not decode JSONL strings. The event-ID checks call it on the enclosing session object, whose event/sample arrays contain strings. Consequently the scripts' recursive-search claim does not itself validate key absence inside those encoded records. The absence stated above comes from separate static inspection of decoded retained records.

The scripts also use numeric comparison and boolean conversion rather than a complete exact-type schema validator, and count every sample above the initial kill baseline rather than deduplicating kill transitions. These limits do not introduce positives into this hash-pinned all-zero corpus, but must not be read as repaired synthetic v2 type gates or a validated general task-effect contract.

## Lineage and navigation

- [Original #4193 owner](https://github.com/Unjuno/agent-interface/issues/4193), [original retained report](../../map01_v12_attack_task_effect_live_v1/REPORT.md), and [original publication correction](../../map01_v12_attack_task_effect_live_v1/PUBLICATION_CORRECTION.md)
- Historical synthetic v1 record at [commit 2d643403](https://github.com/Unjuno/agent-interface/blob/2d643403e729120ce00f0f98d540a5209a2f9b44/research/doom/map01_task_effect_receipt_boundary_4193_successor_v1/results/formal-01/RESULT.md)
- Historical synthetic v2 freeze at [commit 2d643403](https://github.com/Unjuno/agent-interface/blob/2d643403e729120ce00f0f98d540a5209a2f9b44/research/doom/map01_task_effect_receipt_boundary_4193_successor_v1/v2/FREEZE.json)
- Preserved v2 review findings: [type/schema note](https://github.com/Unjuno/agent-interface/pull/5389#issuecomment-5909224298) and [source/denominator note](https://github.com/Unjuno/agent-interface/pull/5389#issuecomment-5909285687)

The six-file v3 diff does not contain v1/v2 files. The inspected v3 head's parent directory contains only `v3/`; historical v1/v2 links above are commit-pinned history, not files in this package. Their construction claims remain qualified by the prior review findings and are neither repaired nor newly validated here.

## CI and continuation boundary

The successful [workflow run 36703869544](https://github.com/Unjuno/agent-interface/actions/runs/36703869544) names exact head `68f75c7ef045cf46168ef89801b55a63a6b077a4`. Its single replay-gate job checks out and runs the unrelated `research/doom/test_map01_scorer_scheduler_replay_3270.py` test. It does not parse v3 `RESULT.json`, run v3's runner/auditor, or validate this publication. It is not v3 artifact validation.

Archival integration is allowed to preserve and navigate this evidence only. Keep #4193's consumed first allocation immutable. No archival merge, comment, or this qualification authorizes a rerun, replacement, source correction, Docker/OrbStack/game/input/provider action, or fresh live allocation. Any matched live recovery/control study still requires an explicitly frozen successor scope, named owner, and exact resource assignment. The broader [#59 goal](https://github.com/Unjuno/agent-interface/issues/59) remains unmet by this archive.

