# S4 audit-only result: synthetic image-equivalence boundary

Issue: [#6030](https://github.com/Unjuno/agent-interface/issues/6030)  
Allocation: `VISUAL-EQUIV-5905-S4-20261001-AUDIT-01`  
Predecessor raw candidate: [S3 candidate output](../looming_yield_5905_visual_identifiability_v3/candidate.jsonl), SHA-256 `FC900DC159087B6A07EABCDF5433E43F0CCBD8DF41EE31C2F8C3E74B81ABF4B0`.

## Result

The one S4 auditor-only invocation exited 0 and returned **`PASS_VISUAL_EQUIVALENCE_BOUNDARY_SCOPED`**. It independently reconstructed six of six exact timestamped raster pairs, verified all six hidden truth pairs (approach contact after the observed 700 ms horizon versus animation with no contact), and matched all six paired cue outputs. The four frozen corruption controls, including truth-label mutation, were effective.

| Cue | Approach yields | Animation false-yields on identical input |
|---|---:|---:|
| Any pixel change | 6/6 | 6/6 |
| Endpoint apparent-radius growth | 6/6 | 6/6 |
| Radius-derived tau | 4/6 | 4/6 |

These paired outcomes demonstrate the declared observational-equivalence limit for this image-and-timestamp-only deterministic observer: for these exact pairs, a cue cannot distinguish approach/contact semantics from the visually identical animation. The candidate was **not** rerun in S4; S4 audits only the S3 candidate's exact retained bytes. S3's first auditor failure remains recorded unchanged and is not retroactively erased.

## Integrity and limits

Source parent equals the S4 frozen main SHA. All eight S4 frozen source/input files were read back from GitHub and matched local bytes before execution. At launch, main was `6d34916b31e4a7b26cda339a7ea7439ddb8dfdd4`; its 14 intervening paths were confined to `research/live_control/observer_ipc_freshness_v3/`, with no overlap with governing docs, #5905 predecessor evidence, S3 evidence, or S4 allocation. The source-only loader tests passed 2/2; the auditor does not import the candidate module.

The execution is an audit recovery over synthetic 64×64 monochrome raster streams, not a fresh candidate experiment, prevalence estimate, live visual-recognition result, GUI/game run, safety outcome, product outcome, or task-effect measurement. It ran host-only on Windows with Python 3.12.10; Docker Desktop was unresponsive and no container/shared slot, model/provider, network, GPU or OS input was used. See [`RUN.json`](RUN.json) and [`audit.json`](audit.json) for exact invocation, receipt, raw report and hashes.
