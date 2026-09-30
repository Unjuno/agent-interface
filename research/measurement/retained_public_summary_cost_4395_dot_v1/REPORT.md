# First outcome: STOP_CLOCK_GRANULARITY

## Decision

The one approved retained-input invocation stopped at the frozen CPU-resolution gate and exited1. It is not a completed cost-characterization PASS. No retry, larger batch, discarded sample, source tuning, new GUI input or model call followed.

-54 warmup calls,162 measured calls and9 separate traced-allocation calls:225 total
-54 measured three-call aggregates
-42 CPU aggregates exactly0ns; the other12 range3,997,976–4,001,391ns
-Reported CPU resolution1ns; empty CPU-bracket median0ns
-Frozen aggregate minimum29,100ns; all42 zero CPU intervals fail it
-Outer stdout/stderr are empty; EXIT.txt records1
-Actual affinity one CPU (0), RLIMIT_AS268435456 bytes, RLIMIT_CPU15s; outer timeout30s
-Peak process RSS15232KiB is an observed resource receipt, separate from the traced-allocation observations

All34 source/input/provenance hashes remain exact. Source-before equals source-after, input object before/after hashes agree, and every output digest in the final receipt matches retained bytes.

## What the raw-only baseline check established

The baseline auditor returned exactly42 CPU-granularity errors and no other error. On these exact inputs, all9 case/policy outputs matched the finite semantic oracle; every repeated output hash was stable; all required source, outcome, session, call, image, capture, release and activation fields were preserved.

The actual refusal stayed byte-identical in all three choices (SHA256e798af97e13d88f9282f46e0c36140a480cf1aa3a6ca743e0076d4ed466de921). Nonpaced save through PACED_BRIEF stayed byte-identical to FULL_V3. The two public summaries matched the historical delivered summaries under typed canonical JSON comparison. Their current wire hashes are separately retained; canonical equality is not a claim that historical field insertion order or wire bytes were identical.

The post-baseline twelve-control block was deliberately not entered after the STOP. All twelve were effective in the explicitly fabricated construction-ledger test, but that is not the completed scientific control gate. Do not upgrade this allocation on the strength of partial gates.

## Retained descriptive observations under STOP

External metadata uses actual MCP JSON defaults, not compact canonical separators. Images/SDK envelopes are outside this boundary.

|Actual retained role|FULL_V3 bytes|PACED_BRIEF bytes|PUBLIC_SUMMARY bytes|
|---|---:|---:|---:|
|Paced entry|9807|6112|4035|
|Nonpaced save|4966|4966|3947|
|Backend refusal|2740|2740|2740|

The nine separate one-call memory observations are also retained, with no population inference. Peak traced Python allocation bytes, holding the projected object and serialized bytes alive:

|Role|FULL_V3|PACED_BRIEF|PUBLIC_SUMMARY|
|---|---:|---:|---:|
|Entry|20504|85970|76062|
|Save|10822|41364|36658|
|Refusal|6370|12642|10930|

These are not total process memory, a cache bound or production overhead estimates. Source input objects/imports were outside tracing. No CPU ranking, CPU speedup, end-to-end latency, token/cost benefit or default-adoption recommendation is supported. Wall samples remain losslessly retained but are not substituted post hoc for the failed registered joint measurement gate.

## Clock discrepancy

A separate parent-authorized generic arithmetic capability check had32/32 nonzero process and thread CPU intervals around1.38–1.87ms. Both that check and this study use direct process_time_ns; frozen visual evidence also uses that API and showed roughly4ms increments. Source/units comparison did not explain the discrepancy.

The capability check justified only trying the frozen protocol with its hard guard. It did not promise that smaller batches would be resolvable. This first outcome now shows the registered three-call CPU measurement was inadequate in the study process. Preserve both observations; do not claim a global environment clock change.

A future measurement would need a new independently reviewed allocation/protocol, with a fixed larger technical batch or a different validated accounting boundary. This result does not authorize such a rerun. Parent decides whether this narrow cost question warrants further work.

## Exact identities

Final freeze:0615d2d5e0cf550c228bf4c2a8cf23b35af26126f878506ed2f4e3cb002e9fe9
Raw:beed605218c471a184a679f03c03159797377f156fb36c49a8fedf741b65c1ff
Audit:727dc56c7b9ddc1a7b967f876866c62a4c0a06ed52a4bc649a8ec4541b96e130
Result:c0052428e9037dac5a0077d6ddb4394b67274b05bfdab0517c6bbab77fe1acd9
Receipt:c8e5d7a1d98ec4bc86f6e1c5dc486572ab128458a146624ef69fa7b094b92a3d

Source main recheck32db1c3fdc6e50dd6d64c3d6886e503c94144fd6; exact upstream blobs are in SOURCE_ACQUISITION.json. Original real corpus archive SHA256b44b25eadd1fc17d0ebcd4b5ce13ae18750c3cd1e127c5bb6f377ac1be3514d3. Earlier proposed freezes, pre-run review corrections, construction failures and capability observations remain additive and unchanged.

