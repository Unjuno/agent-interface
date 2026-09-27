# Online LoRA update-schedule comparison

Issue: [#4888](https://github.com/Unjuno/agent-interface/issues/4888)  
Allocation: `needle-online-correction-cadence-20260927-v1`  
Formal seeds: `734211, 734311, 734411`  
Controlling amendment: v3 comment on Issue #4888.

This is a new allocation following the invalid #4824 formal STOP. The original schedule was superseded by v2 after construction seed 734011 showed no B acquisition. The v2 constant-A/Gaussian task was superseded by v3 after construction seed 734012 showed neither arm acquired B or retained A and source comparison found that task unlike the established correction frontier. Both construction outputs are preserved separately and excluded from formal evidence. Predecessor sources/results remain unchanged.

## Task and splits

Each seed uses 8 features: feature 0 is balanced binary; features 1–7 are seeded uniform floats in [0,1). The hidden-16 tanh classifier has four output logits; role A labels are feature 0 and opposing role B labels are `1 - feature0`. Independently seeded, row-disjoint streams contain 256 A-base-training rows, 16 balanced B support rows, 256 held-out A rows, and 256 held-out B rows. The auditor regenerates every stream, label and base-training row index, and checks exact cross-split row non-overlap. Construction-only seeds 734011, 734012, 734013 and 734014 are all excluded from the formal block; 734014 validates the independent audit path on complete raw evidence.

Train the base only on A-base-training rows: exactly 400 single-row AdamW steps, lr 0.03, weight decay 1e-4. Freeze its tensors. Two rank-2 output LoRA arms start from the same base and adapter initialization (left factor normal std 0.1, right factor zero), each with fresh AdamW (lr 0.04, weight decay 1e-4). The shared 16-row B stream is kept in one fixed order.

## Equal-step treatment

- SINGLE: on each feedback arrival, run exactly 8 updates using only the newly arriving row; 16 arrivals, 128 optimizer steps.
- MICROBATCH2: after the second row of each adjacent pair, run exactly 16 updates on the two-row batch; 8 pairs, 128 optimizer steps. No update occurs after the first row of a pair.

Both arms are scored after every arrival on the fixed held-out A/B sets. Record every adapter and AdamW state, row prediction, per-step duration and per-feedback update-burst duration. This is a comparison of two equal-step schedules; it is not an isolated batch-size causal estimate or an end-to-end acknowledgement-latency measurement.

## Gates and boundary

Apply Issue #4888's v2 decision thresholds as clarified by v3: SINGLE final B >=0.85; MICROBATCH2 final A and B >=0.90; MICROBATCH2 B no more than 0.10 below SINGLE for each seed; mean MICROBATCH2 final-A gain >=0.05 over SINGLE across the three seeds. Also require exact independent data/model/optimizer replay, base immutability, unknown-role and stale-scope YIELD without proposal, exact source/invocation/raw binding, zero independent-audit errors and each individual optimizer update <60 ms. A burst is reported separately.

Use only cached Docker image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64 CPU, one thread, no network, no pull, read-only root/source, 1 CPU, 2 GiB and 64 PIDs. Construction-only seed 734013 is excluded. Exactly one formal trainer orchestration and one separate independent auditor; no retries, tuning, seed replacements, provider/network, GUI/user data, product/runtime changes or action authority. See the Issue for typed PASS/FAIL/HOLD/STOP decisions and limits.
