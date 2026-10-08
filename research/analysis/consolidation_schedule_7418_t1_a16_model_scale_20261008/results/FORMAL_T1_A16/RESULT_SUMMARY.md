# A16 model-scale and schedule-sensitivity result

Status: **PASS_METHOD / PASS_CADENCE_SENSITIVITY_SCOPED**. The Qwen3 14B candidate completed all 390 registered calls; the independent auditor found zero transition, provenance, row, schema, or identity errors. The 8B-to-14B transition was not tested with paired seeds, so the clean audit is consistent with a model-capability explanation for A15 but does not isolate model scale causally. The within-A16 cadence result is consistent across all three fresh seeds under the frozen >=0.10 paired-difference rule inherited from A13.

## Exact-answer accuracy at every checkpoint

Each cell is correct exact answers out of 15 (five queries × three seeds).

| Schedule | Prefix 1 | Prefix 2 | Prefix 3 | Prefix 4 | Prefix 5 | Prefix 6 | Mean across 30 answers/seed |
|---|---:|---:|---:|---:|---:|---:|---:|
| episodic_only | 12/15 | 15/15 | 15/15 | 12/15 | 9/15 | 9/15 | 0.800 |
| per_episode | 9/15 | 12/15 | 9/15 | 12/15 | 9/15 | 9/15 | 0.667 |
| batch_2 | 15/15 | 12/15 | 12/15 | 12/15 | 9/15 | 11/15 | 0.789 |
| terminal | 15/15 | 12/15 | 9/15 | 6/15 | 6/15 | 9/15 | 0.633 |

Per-seed means: episodic-only 0.800/0.800/0.800; per-episode 0.667/0.667/0.667; batch-2 0.800/0.800/0.767; terminal 0.633/0.633/0.633. Four consistent >=0.10 contrasts qualified: episodic-only over per-episode (+0.133 each seed); episodic-only over terminal (+0.167 each); batch-2 over per-episode (+0.133/+0.133/+0.100); batch-2 over terminal (+0.167/+0.167/+0.133). Episodic-only and batch-2 did not differ by the registered margin.

## Cost, memory, and exception/query diagnostics

Figures below are means per seed-arm over three seeds except rates explicitly shown as counts. Calls include 30 fixed query calls plus the schedule-specific number of consolidation calls. Token totals include query and consolidation prompt/completion tokens. Recorded elapsed time is the sum of request durations, not end-to-end wall time. Serialized memory size is UTF-8 bytes in each consolidation response.

| Schedule | Calls | Query tokens | Consolidation tokens | Total tokens | Request seconds | Consolidation states; mean/max bytes | Rare-exception exact answers (prefixes 3–6) | False non-UNKNOWN on oracle UNKNOWN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| episodic_only | 30 | 11206 | 0 | 11206 | 51.0 | 0; n/a | 3/12 | 6/51 |
| per_episode | 36 | 9960 | 9108 | 19068 | 122.1 | 6.0; 660/1213 | 9/12 | 15/51 |
| batch_2 | 33 | 9177 | 4711 | 13888 | 79.1 | 3.0; 744/1213 | 8/12 | 3/51 |
| terminal | 31 | 7123 | 1851 | 8974 | 51.2 | 1.0; 1213/1213 | 0/12 | 0/51 |

The exact answer to the rare-exception query was correct in 3/12 episodic-only, 9/12 per-episode, 8/12 batch-2, and 0/12 terminal checks at prefixes 3–6. Despite these query misses, the transition auditor found every stored exception claim faithful. Thus memory-write faithfulness and downstream answer behavior are distinct endpoints here. Across the full 360 queries, false non-UNKNOWN answers on oracle-UNKNOWN cases numbered 6/51 episodic-only, 15/51 per-episode, 3/51 batch-2, and 0/51 terminal. The independent transition audit found zero unsupported/malformed memory claims on this finite fixture.

## Interpretation and limits

On this synthetic source-bound ledger and this Qwen3 14B configuration, update schedule was not behaviorally innocuous: frequent per-episode and terminal schedules scored below episodic-only or batch-2 in consistent held-out exact-answer contrasts, while episodic-only and batch-2 were within the registered margin. The method gate passed, so this is a scoped cadence-sensitivity result for this fixture, prompt, model, and seeds. It does not establish that larger models generally solve transition fidelity, that any schedule is optimal in other corpora, or that GUI agents/users benefit. No action was executed.

Frozen allocation: `GUI-MEMORY-CONSOLIDATION-SCHEDULE-8406-T1-A16-MODEL-SCALE-20261008`; freeze commit `6704f9cf`, preregistered before inference in Issue comment `6052082917`. Result artifacts and posthoc checkpoint calculations are in this directory.

Raw SHA-256: `5d88e0a1cdfe05a99c5e2e42189fc47be611d7abf237e52fb5e556e3069881dd`  
Audit SHA-256: `6d7770dc7ff7c3d78515362a50b7ec10ea86e62c67fddf303716682ebbc0c240`  
Preflight SHA-256: `01c953bf4a61c50a80149b1abba57bf81a5c6047f54a7e6d3b3a077ca68416f4`  
Checkpoint metrics SHA-256: `606b89f38258aa4368c989a4e93fa3db4afba8af908e9d86157a89a8033f6f53`  
Audit status: `PASS_METHOD`; decision: `PASS_CADENCE_SENSITIVITY_SCOPED`; errors: `0`.
