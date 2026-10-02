# Archival qualification: multimodal grounding T0 construction (#5300)

This is historical corpus/protocol preservation only. It does not establish model grounding, accuracy, latency, tool-isolation execution, Astra equivalence, task success, or production authority. The original 27 files are preserved byte-for-byte; this separate note does not repair or reinterpret their contents.

## Identity and retained scope

- Source: [PR #5300](https://github.com/Unjuno/agent-interface/pull/5300), head `ec3112ec7e3fdacd0f097719d07b2a81e91ed429`, branch `research/multimodal-grounding-5263-t0-20260930`
- Original directory: `research/system1/multimodal_grounding_5263_t0_20260930/`
- Original directory tree: `7d109b8765d66cc965b250d41be96aae968c91cf`; image tree: `c929bbe5a9b39089f416e73437737edea3f18cc5`
- Original intake main: `c45e1947e498dce08abfb27e459e610054a0602e`, as retained in [ENVIRONMENT.json](ENVIRONMENT.json). Archival placement on a later main does not create a new formal freeze
- Owner: [Issue #5263](https://github.com/Unjuno/agent-interface/issues/5263), still open at archival review on 2026-10-01; source PR still open/Draft

The 13 text files retain the preregistration, prompt, image/intent manifest, separate oracle, category definitions, renderer and historical font/model/environment identities, closed-root output schema, protocol/scoring helpers, comparator argv builder, test sources, and append-only status chronology. The 14 PNG paths represent seven categories with two cases each. There are 13 unique PNG blobs: c01 and c05 intentionally share the same screenshot bytes while their intents differ. None of the images was regenerated or re-encoded for this archive.

Data-only archival checks reproduced every original Git blob ID and source-tree byte length/mode. All 14 PNG SHA-256 values agree with [cases.json](cases.json), and their headers declare 1280x800, 8-bit RGB. The package/image Git tree identities were also reconstructed from the original entries. These are byte-preservation checks, not execution of the retained tests or scientific validation of the corpus.

## Historical test and comparator claims

[STATUS.md](STATUS.md) preserves the initial 10/10 host/Docker construction claims, the initial `HOLD_NO_QUALIFIED_COMPARISON_ROUTE`, the Docker coordination deviation, and the later correction of the mistaken statement that Codex CLI had no tool-disabling controls. The owner subsequently reported a configuration-only feature check and 15/15 host tests in the [comparator correction](https://github.com/Unjuno/agent-interface/issues/5263#issuecomment-5907697705). Those are historical reported observations. The 27-file package contains no separate original test stdout/stderr, configuration-check transcript, raw model responses, inference timing stream, or independent formal raw audit. No tests, feature checks, renderer, scorer, model, container, or experiment were run during archival preparation.

The amended candidate is `gpt-6-astra` through a Codex CLI wrapper whose [frontier_profile.py](frontier_profile.py) constructs tool-disabling arguments. It is expressly not the project's separately hosted Astra grounding service. Argument construction and historical host checks do not demonstrate an executed inference boundary, actual tool isolation during model calls, comparator equivalence, or model performance. Earlier GPT-5.6-Luna proxy wording and its later correction are retained as chronology, not silently rewritten. The source PR's current recorded disposition is `HOLD_NO_FORMAL_RUN_RESOURCE_AND_FREEZE`, with zero model calls/inference results.

The closed JSON Schema and [protocol.py](protocol.py) play different roles: the schema closes the root object, while the protocol validator constrains cross-field combinations. The scoring and median helpers are preparation, not a retained execution of every formal decision gate.

## Resource-coordination deviation remains attached

The [owner disclosure](https://github.com/Unjuno/agent-interface/pull/5300#issuecomment-5907324879) records that the 10-case Docker construction invocation and brief Ollama preflight used the shared Docker resource during #5139's exclusive 2026-09-30 08:16–08:30 UTC allocation. The source reports no inference, model load, CUDA/GPU call, fit, or persistent model-store write in those invocations. Even so, they were not authorized by that lease and are not lease-compliant evidence. Preserve them only as construction observations with this deviation attached. Archiving their source does not retroactively authorize them or inherit a released slot.

## Formal gates remain unrun

[PREREG.md](PREREG.md) proposes one finite, single-pass/no-replacement comparison of the same frozen image bytes and bounded intents. Its gates require all six safe cases (c05–c08 and c13–c14) exact, no wrong target/container, at least 7/8 other cases exact, all outputs parse/schema-valid, and local median warm end-to-end latency at most 0.5 times the comparator median across all 14 paired cases. Cold first-request latency is separate. Any unsafe abstention failure or wrong target cannot be rescued by speed. These thresholds are proposed criteria, not observed outcomes.

Any later formal work still requires a fresh current-main source/corpus/prompt/schema/model/API-identity/image/output freeze, sufficient verified storage, collision checks, and the exact applicable resource authorization. Inventory snapshots and an idle device are not leases. No model output grants input authority; later actions still require ordinary target/focus/surface/deadline/release admission. No general Astra-free, arbitrary-GUI, temporal, human-tempo, or production claim follows from this synthetic corpus.

## Related work is separate

- [PR #5353](https://github.com/Unjuno/agent-interface/pull/5353) is the separately scoped LM Studio/Gemma adapter construction, with hand-authored loopback mock responses. It neither replaces this Qwen/corpus proposal nor satisfies #5263 T0
- The later [CPU-only LM Studio load attempt](https://github.com/Unjuno/agent-interface/issues/5263#issuecomment-5908419330) stopped at 4% with `ENOSPC`; it produced no inference request/output. That later attempt must not be conflated with this source package's earlier zero-load preflight record
- [Issue #5453](https://github.com/Unjuno/agent-interface/issues/5453) holds perception fixed while varying downstream decision policy. It is not this corpus's formal result or a grounding replacement

At pinned archival-review main `0afd3e33b9da5e8ed4c8307609fec3264d4b93f2`, this original directory was absent, none of its 27 original blob IDs occurred in the complete System-1 subtree, and searches for #5300/#5263 found the source and distinct #5353 adapter rather than another archive. This is a scoped point-in-time coverage check; publication requires a fresh collision/index check.

Preservation adds no runtime path, rerun authorization, source-PR readiness change, or owner-issue closure. #5300 remains historical construction/preparation; #5263 remains open.
