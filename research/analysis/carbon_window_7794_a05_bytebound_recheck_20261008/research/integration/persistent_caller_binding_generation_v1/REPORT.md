# Persistent caller unified binding-generation conformance v1

## Decision

**PASS_PERSISTENT_CALLER_UNIFIED_GENERATION_CONFORMANCE_SCOPED**.

This is an integration/conformance result for Issue #774, following the real-X11 `PASS_UNIFIED_BINDING_GENERATION_SCOPED` result retained under Issue #57. It tests the exact retained `adaptive_acquisition_caller_v2.py` cache/repair route together with exact `scoped_target_handle_v1.py` generation-scoped target evidence. It does not rerun X11 lifecycle discovery or claim model/token benefit.

## H / T / D / C / U frozen before formal

**H.** A persistent cached symbolic target must carry the same caller-owned binding generation used by runtime action freshness. If the current generation is supplied at both reuse and final target revalidation, every generation transition should make the old handle stale, drive the existing repair path, and execute only a fresh-generation target. Stable same-generation reuse should remain model-free. A comparator that leaves target scope on the cached generation should carry the stale symbolic target to the execution fence.

**T.** Byte-exact retained/current `adaptive_acquisition_caller_v2.py`, `scoped_target_handle_v1.py`, and `coordinate_frame_transform_v1.py` were used. The deterministic fixture keeps focus XID=101, surface XID=202, geometry, observation sequence and RGB target patch identical across a restart; only the caller-owned generation advances. Construction exhaustively covered all 64 length-6 binary traces and was excluded. Formal then ran once over every `2^13 = 8,192` stable/restart trace, both arms, for 212,992 adaptive-caller task executions. Every formal trace was retained; no sampling, retry, replacement, extension or threshold tuning occurred.

**D.** PASS required candidate success106,496/106,496, stale target presentations to execute0, safe stops0, stable-path model calls0, and exactly53,248 repairs/model calls for the mathematically expected53,248 restart events. The revision-only comparator had to expose stale symbolic presentation in all8,191 restart-containing traces, with aggregate stale presentations98,305. Independent audit had to recompute every trace.

**C.** This fixture assumes an authoritative generation transition already exists. The execution reference fence represents the runtime binding-revision contract retained by the preceding live work. The question here is where the persistent caller must invalidate/repair cached symbolic evidence, not how lifecycle changes are detected.

**U.** Single-process deterministic composition only. No Chromium/X11/provider timing, actual model quality/usage, second-domain effect, final check-to-input atomicity, or production reliability is measured.

## Source-first closure

Immutable publication BASE: `be33a94034bd26703726d6474af327d9a171a905`.

Before formal, the complete source/config archive was pushed and remotely read back on the dedicated branch. Remote source archive Git blob: `b266ad5654babed3fe32aa8ea32870eee35b3e4a`, 15,885 retained bytes. `FREEZE.json` Git blob: `4b156560bb96cd171b6355f04eab1b6c3b1bd482`. Formal cases at that point: 0/212,992.

Exact upstream Git blobs were preserved:
- adaptive acquisition caller v2: `176b342913ea6b5b704d4c986d5ddbf1dbcd8169`;
- scoped target handle v1: `c4482bb7cd9c3a3e780c05bafa34073491a33ece`;
- coordinate transform v1: `972daffee40a38d3effbd8155f3da133d664e445`.

Construction: 64/64 length-6 traces. Candidate tasks384/384 succeeded, repairs192, stale-to-execute0. Revision-only stale-to-execute321, and every restart-containing construction trace (63/63) exposed the intended negative control.

## First formal outcome

One formal invocation completed all 8,192 traces in 24.65 s wall time in this container (descriptive harness time only; not product latency). Maximum recorded process RSS was 96,684 KiB.

| Metric | revision_only comparator | unified_generation candidate |
|---|---:|---:|
| traces | 8,192 | 8,192 |
| adaptive-caller tasks | 106,496 | 106,496 |
| TASK_SUCCEEDED | 8,191 | **106,496** |
| safe stops | 98,305 | **0** |
| stale target presented to execute | 98,305 | **0** |
| repairs | 0 | **53,248** |
| model-stage fixture calls | 0 | **53,248** |
| stable-path model calls | 0 | **0** |
| restart events | 53,248 | 53,248 |
| restart traces with comparator counterexample | 8,191/8,191 | n/a |

The comparator's 8,191 successes are the stable-prefix executions before the first restart across the complete trace space; after a first restart, its unchanged cached symbolic target remains observationally eligible under its old scope but is rejected by the execution binding fence. The candidate instead observes `SCOPE_MISMATCH`, maps that to the caller's already-typed `stale` decision, invokes the existing repair branch exactly once for each restart event, then final-revalidates and executes the newly bound generation.

This result therefore supports a narrow integration rule: **the persistent caller cache should store target evidence as part of a binding snapshot whose generation is the same generation used for action/program freshness.** The repair machinery already present in the caller is sufficient in this fixture; no second identity system or new executor was needed.

## Independent audit and mutation controls

The frozen audit parses the raw 8,192-row trace log and independently derives the expected metrics from each 13-bit trace. It verified:
- exactly8,192 unique traces and complete binary coverage;
- candidate per-trace repair count equals that trace's restart count;
- candidate stable-path model calls are always0;
- comparator success/stale split is exactly determined by the first restart position;
- aggregate counts match the preregistered values;
- all seven frozen source/config SHA-256 values still match.

Audit: PASS, errors0. Formal result SHA-256 `70fa61dbb273f3c95fa2ac2d259ce75d3a6b6e1016606ad5636aa5348cf45592`; raw trace-log SHA-256 `0115b1d9f0d607114782558f84e56d408b65743fd3f0af5a2677a7d3fb620aa7`; audit result SHA-256 `48ed394f4646fc1e3d283ff72fab5a97f21a43fba5d379fb7b2bf584b2e1aec5`.

Six copied-evidence corruptions were all rejected: candidate stale presentation, stable-path repair/model call, comparator stale aggregate mutation, missing trace row, one per-trace candidate repair mutation, and duplicate/missing binary trace coverage.

## Interpretation boundary

This closes the mechanism-level caller/cache composition gap exposed by #57: two independently valid freshness epochs should not be managed separately at the persistent caller boundary. The caller-owned generation can feed both the action binding revision and target-handle session scope; generation transition invalidates the cached reference and the existing repair branch performs an explicit fresh rebind.

It does **not** establish that the historical live `integrated_efficiency_client_v1.py` has already been modified or productized with this state. It also does not create a supported authenticated model path for the remaining second-domain economic evaluation. Those are separate integration/deployment questions.
