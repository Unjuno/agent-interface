# T1-A18 independent-seed replication of A16

A18 repeats A16's frozen schedule evaluation with the same Qwen3 14B Q4_K_M model digest, prompt, schema, episode fixture, query set, schedules, decoding and auditor. The only planned change is a fresh numeric seed set (5701/5702/5703). The goal is to test whether A16's clean transition audit and scoped schedule differences recur beyond its original three seeds.

The candidate has one 390-call allocation, followed by one independent audit only if all calls complete. A17's separate 8B failed-audit output is excluded. Same-model seed replacement does not establish corpus or model-family generality. No generation retries, output repair, pooling, GUI input, user data, action authority, or external effects are involved. `PROTOCOL.md`, `FREEZE.json`, and `RUN_RECORD.json` define the gates and hashes.
