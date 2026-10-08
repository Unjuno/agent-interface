# T1-A17 paired-seed model-scale check

A17 repeats A16's frozen schedule evaluation with Qwen3 8B instead of Qwen3 14B, using the same seeds 5601/5602/5603. This seed-matched follow-up tests whether A16's clean transition audit and scoped cadence differences are robust to model scale under the same prompt and fixture.

The prompt, schema, fixture, query set, four schedules, decoding, auditor, and seed values are byte-identical to A16. The sole treatment variable is model scale (both variants Q4_K_M); all outputs remain separate from A16. The candidate makes 390 calls once, followed by one independent audit only if all rows complete. See `PROTOCOL.md` and `FREEZE.json` for exact gates and hashes.
