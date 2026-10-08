# Role-conditioned online LoRA rehearsal

Issue #4895; allocation `needle-online-lora-role-rehearsal-20260927-v1`; frozen source and gates are recorded in `FREEZE.json` and #4895.

Three fresh formal seeds: 735211, 735311, 735411. Construction seed 735014 is excluded. Each row has eight task features and a final explicit role feature (A=0, B=1). The A base is trained only on A-role rows; the B feedback rows carry role B and the complementary binary label. A disjoint 16-row balanced A reservoir is retained for the rehearsal arm. A/B held-out splits are disjoint from training, memory and support.

The frozen base is trained for 400 deterministic single-row AdamW steps. Each fresh rank-2 LoRA arm gets 16 B arrivals and exactly eight AdamW steps per arrival (128 total): B_ONLY uses the current B row, B_DUPLICATE_CONTROL duplicates that row, and A_REHEARSAL pairs it with one cyclic A-memory row. All arms use identical initial base/adapter weights and fresh identical AdamW settings. Score at every arrival.

The primary contrast is A_REHEARSAL vs B_DUPLICATE_CONTROL. The duplicate arm matches tensor batch size while adding no new examples; B_ONLY is descriptive. PASS requires all seeds' replay arm final held-out A/B >=0.90, its B within 0.10 of duplicate control, and mean final-A gain >=0.10, plus exact independent replay, immutable base, YIELD controls, provenance and per-update <60ms. See Issue #4895 for typed decisions and scope.

Construction tests perform zero optimizer updates. Formal training occurs exactly once in the locally cached pinned CPU Docker image, network-disabled, read-only source/root and bounded resources. A separate Docker invocation independently regenerates and replays raw data, states, predictions and gate decisions. No retries, tuning or seed replacement.
