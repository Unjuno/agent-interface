# T0 run ledger

Frozen source/image: main `7c6f610fe73fe8135895e8715a81053ffb46b2a7`; WSLc `3.0.1.0`; image ID `sha256:1b4a8bd7c0fe372cc0cafa74af433b8ae1f73f1bee0f11a028f126b08b2c128a`.

1. Focused tests, WSLc network-none, read-only source: 12/12 PASS normally and 12/12 PASS under `-O` before the final fabricated-success mutation was added.
2. Candidate/auditor, separate Python processes, read-only `/src`, writable `/out`: candidate exit 0, 96 rows; independent auditor exit 0, accepted 96/96. Candidate stdout SHA-256 `2a32089fe2c11313966f8e0a9b00286e33026c5a477c7d3ec7d55e439cc0529d`; audit stdout SHA-256 `71aa6dbcb27dbb582723146075066e4791707c4d57ced854d936147d9f660d4a`. Output files retained under `results/`.
3. A first aggregation command failed at PowerShell/Python argument quoting, before candidate/auditor launch. The repaired read-only summary invocation succeeded; see the retained limitation in `README.md`.
4. Added one final adversarial test that falsifies success when both channels fail and rediscovery is unavailable. Final suite was rerun after this change: 13/13 normal and 13/13 under `-O`, both PASS. Candidate/auditor source and frozen fixture were unchanged, so first outputs were preserved rather than overwritten.

Container emitted the cgroup/swap-limit warning on every call; no hard memory cap is claimed. No model, GUI, or side effect ran.
