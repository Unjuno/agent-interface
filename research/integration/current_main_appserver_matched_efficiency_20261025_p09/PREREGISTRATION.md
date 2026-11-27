# P09 preregistration — matched direct-input / compiled-caller efficiency

Status: preregistered before any provider call. P06–P08 remain immutable and are not replayed. This is a new paired comparison on synthetic Fake X, with six one-shot arms in three counterbalanced pairs.

## Question

Under matched visual/model/session conditions, how do direct `interface_guarded_input` and `interface_guarded_compiled` compare on successful independent task effect, verified release, provider usage/latency, and caller wall time?

## Frozen conditions

- Six trials: three fresh pairs, three per arm. Pair order is frozen as direct/compiled, compiled/direct, direct/compiled. Each trial gets a new independent session and one model generation with no retry/recovery. Model `gpt-6.1-sol`, effort `low`; retain App Server protocol and usage updates.
- Current-main source is the exact repository commit recorded in `PRELAUNCH.json`. Windows CPython 3.13.14; same-process public MCP server and `RecordedPublicMcpCaller`; child-owned Fake X transport. Each arm uses a fresh process/session but identical deterministic visual task and effect oracle.
- The public observation image is the image shown to the model. It depicts three small labeled colored targets. Prompt names the green target but supplies no coordinates, alias, profile, or compiled action JSON.
- Both arms use the same two-integer screenshot-point schema and exact public-observation image, the same prompt and exact source-sequence mint. Direct arm calls `interface_guarded_input(interaction="click")`; compiled arm executes the preregistered one-transition `interface_guarded_compiled` click. The synthetic app changes a pixel only for an owner-side XTEST click inside the green target. Independent success requires the selected/clicked point, exactly one effect, expected final pixel and verified neutral release.
- Measure each model turn's reported usage and duration, observation-to-action-return latency, total trial time, tool call count, and compiled transition count. Compare paired differences within each counterbalanced pair. No run may be replaced; any failure/unknown counts against its arm and remains preserved.
- No WSLc, Docker, physical input, or unrelated user application. This compares two caller routes on synthetic Fake X; it does not qualify live GUI, MAP01, blocked-I/O recovery, cross-domain transfer, or broad reliability.

## Decision rule

An arm trial passes only with one completed model turn, protocol/provider/ledger usage agreement, exact image hash, point inside target, mint on the observed sequence, exactly one owner-side click/effect, expected final pixel, verified neutral release, complete ledger and valid raw hashes. The paired study reports all six results, per-arm pass counts, median and paired latency/token differences, and exact binomial uncertainty. Runtime `task_success` remains null. Three pairs are exploratory descriptive evidence, not a broad reliability estimate.

## Retention

Retain per trial: exact observation PNG, App Server protocol/usage, provider request/response, public MCP envelopes, selected point, mint/action receipts, owner click/effect, initial/final image, release/close receipts, ledger, score and hashes. Preserve all six first outcomes. This packet provides a first matched efficiency/reliability sample only; physical/live application, blocked-I/O release, WSLc transfer and MAP01 remain open.
