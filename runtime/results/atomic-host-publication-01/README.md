# Exclusive Linux host JSON publication

Integration decision: adopt the existing native-exchange file publication mechanism as an optional portable CLI/Python host utility. Keep **HOLD_INTEGRATION_INCOMPLETE** for the six-task matched comparison required by [#2789](https://github.com/Unjuno/agent-interface/issues/2789). This increment addresses the primary-review handoff between committed input and the next task; it does not establish acceptance of the whole spine.

## Concrete failure and change

The primary operated the unchanged six-task research harness using the current portable runtime, source `bc1ca7f316d86ecaee5f24b3f961b69f8be32eae`, seed 991609, persistent then direct, fresh private X11 allocations. Public Python dispatch handles navigation/direct action and the public guarded bridge handles persistent targets. This is not a public MCP stdio run. No helper model or subagent was used. The primary supplied screen groundings and outcome decisions.

Persistent completed six exact submissions. At task 4, the layout changed: the old target refused before input, then explicit image re-grounding allowed bounded recovery and later reuse. Direct submitted task 1 correctly, but its review reader stopped with `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`. The host helper wrote directly to the final review filename with Node `writeFile`/`wx`. The failure is consistent with a reader seeing an empty or partial write; the actual bytes read at the failed instant were not captured, so unique historical causation is unproven. The eventually completed authored JSON is retained and is not counted as an accepted review. The failed allocation was not replayed.

The new Linux-only `publish-json --path <fresh-slot> --value -` and `publish_json` expose `encoded` and `publish` unchanged from `research/live_control/native_exchange_v1.py`. The helper writes and fsyncs a private temporary file, exclusively hard-links complete bytes to the final name, then fsyncs the parent. It does not choose actions, grant source authority, dispatch input, install sensors or supply a model. The receiving protocol must still validate its decision/source contract. An error after linking may leave a complete occupied slot: reconcile; never overwrite, republish or replay input based on that error. Cross-filesystem crash guarantees and producer authentication are not established.

## Retained accounting

| Route | Independently exact submissions | Accepted primary reviews | Original terminal result |
|---|---:|---:|---|
| Persistent | 6/6, each exactly once | 6 | outer exit 0 |
| Direct | 1/6; tasks 2–6 missing | 0; task 1 unavailable | outer exit 1 |

The verifier independently compares submitted payloads and layouts with the goal, rather than using the fixture's `exact` flag. It checks 18 completed input release records in persistent and 2 in direct, matching authored review/source sequences and PNG hashes, task-4 refusal/recovery, terminal results, exact source promotion and candidate package bytes. Cleanup is terminal but not uniformly successful: persistent process codes are 0/1/1, direct 0/1/0. Do not convert these into clean-exit claims.

Persistent action-to-local-feedback durations are 539.365, 551.652, 530.068, 28813.279, 544.413 and 577.785 ms; direct task 1 is 253.709 ms. These are descriptive wrapper timings, not a route speed comparison. Task 4 includes primary re-grounding. The cooperative window-title cue is separate from the independent payload scorer and is not generic semantic completion. Primary review intervals include tool scheduling, host waits and commentary; model-visible timestamps and isolated reasoning time are absent. Delivery cadence changed after persistent task 2. Fixed route order allows carryover, and exact model configuration/usage metadata were not available. No human-speed, token/cost, general GUI reliability or causal latency claim is supported.

## Mechanical validation and provenance

The no-GUI publication probe uses the stopped route's authored review only as JSON content in new slots. A deterministic direct-write control observes an empty final file and reproduces the parse error. With the candidate portable archive, the final slot remains absent during partial stdin, the receiver parses the complete exact value after publication, and duplicate publication exits 2 without overwriting. This is not a rerun or recovery of the failed GUI allocation. CLI tests additionally check a gated pre-link write, pre-/post-link fsync failures, duplicate refusal, non-finite JSON and unsupported platforms.

After committing source, 49 CLI/distribution tests passed. The first package test invocation rejected uncommitted new source files (7 distribution errors); this was corrected by committing before building, as required by the exact-commit builder. Final local suites passed: 317 protocol and 135 harness tests. `native/result.json` and complete logs are retained in the raw archive; these checks are not live GUI acceptance.

`raw.tar.gz` retains 375 original allocation, image, native-log and source files without editing the originals. `manifest.json` binds their inventory and hashes. Original and candidate portable builds and their manifests are retained. The candidate executable source is `6ce7dbb19`; evidence source revision `3830178ff` additionally includes the sparse CI closure. The recorded Node helper is a function capture depending on its original REPL bindings, not a standalone reproducibility script. The publication probe records commands/outcomes but its full execution script was not captured. Source snapshots are selected dependencies, not a complete standalone machine/environment capture. Consult the exact repository revision for a fresh allocation; do not resume or overwrite these old slots.

Run `python3 -O runtime/results/atomic-host-publication-01/verify.py`. Verification is read-only, without extraction or input. The next end-to-end check must be a fresh identified allocation using atomic host publication, preserving these STOP and success records. Current comparison and broader product/human-tempo objectives remain open.
