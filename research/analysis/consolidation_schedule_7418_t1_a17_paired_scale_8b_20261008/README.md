# T1-A17 paired-seed model-scale check

A17 repeats A16's frozen schedule evaluation with Qwen3 8B instead of Qwen3 14B, using the same seeds 5601/5602/5603. It tests whether A16's clean transition audit and schedule differences recur at a smaller model scale under the same prompt and fixture. The completed A17 audit returned `FAIL_METHOD` (24 errors), so its accuracy and cost summaries are descriptive only and cannot support a schedule-sensitivity conclusion.

The prompt, schema, fixture, query set, four schedules, decoding, auditor, and seed values are byte-identical to A16. The sole planned treatment variable is model scale (both variants Q4_K_M); all outputs remain separate from A16. The candidate completed 390 calls once with no call errors, followed by one independent audit. A17 failed transition fidelity in each seed on the same two categories: incorrect `ep03` rare-exception values (`draft_saved` instead of `no_external_effect`) and an early `revision-r7-mode` conflict claim in `batch_2`, followed by an explicit-conflict mismatch. The complete error list is in `results/FORMAL_T1_A17/audit.json`.

Mean exact-answer accuracy across seeds was 0.267 (`episodic_only`), 0.533 (`per_episode`), 0.633 (`batch_2`), and 0.667 (`terminal`). These results contrast with A16's 0.800, 0.667, 0.789, and 0.633 respectively, but because A17 failed its independent transition audit, these numbers are descriptive and not valid cadence evidence. Same numeric seeds do not imply coupled random streams across model sizes. No A16/A17 pooling or GUI/product/action inference is supported. See `RESULT_SUMMARY.md` and `RESULT_RECORD.json` for full interpretation, checksums, and costs.

See `PROTOCOL.md` and `FREEZE.json` for preregistration, frozen gates, and source hashes.
