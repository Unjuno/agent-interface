# T5 run log

1. Before freeze, arithmetic review found the expected inherited-row count was 8 rather than the actual 6. Corrected candidate and auditor before freezing; no execution had occurred.
2. Frozen source hashes and pinned Docker image were checked against FREEZE.json.
3. Candidate invoked once in network-none/read-only Docker; exit 0; emitted 256 rows; raw SHA-256 `3d6ad66e2571c2d7b7eec6357b8383d9a8e39b582a1f8cea9927f4d195b2d868`.
4. Independent auditor invoked once in a separate container; exit 0; status `PASS_T5_INDEPENDENT_CLAIM_BINDING_ORACLE`; 256 rows matched; errors=[]; output SHA-256 `7822a02a3b817c95e1393509a9b33d6bb24b14397ea62e49b22068e361c052cf`.
5. Candidate and auditor formal invocations: 1 each. Retries: 0. No source changed after freeze. No live scheduler, model, GUI, cryptography, GPU, or external effect was used.
