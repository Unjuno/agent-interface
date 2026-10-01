# Preparation attempt log

All entries below are pre-model, CPU-only preparation. None is a formal fit, model load, CUDA operation, Docker invocation, or result.

1. Initial wrapper test returned a `ValueError` because it accidentally called the archival sampler-package builder with three seed arguments; that builder has a different `(seed, support_seed, allocation)` interface. It emitted no dataset. The wrapper was corrected to use the current-main formal builder, whose frozen three-seed API matches this preregistration.
2. The first `unittest discover` found zero tests because the checks were plain functions rather than `unittest.TestCase` methods. They were converted to a discoverable test class.
3. Corrected pytest construction suite: 4/4 passed. Dataset generated from the frozen fresh seeds: 805,111 bytes, SHA-256 `2359da75ebe7a96d60a24c215d3d70da4ecc4351c328387a56ac279b41615fa0`.
4. A repeated dataset-generation command returned `STOP_DATA_OUTPUT_EXISTS`; it did not overwrite the already-generated frozen input. The byte-identical data hash was read back.
5. Static review found that a formal invocation failing before its first receipt could leave an empty output directory and permit an accidental retry. The runner now claims an exclusive `FORMAL_ATTEMPT.json` marker after all frozen input checks but before importing PyTorch or calling CUDA. A CPU unit test verifies that a second claim is rejected without changing the first marker. No formal invocation, model load, CUDA call, fit, or adapter update occurred.
6. A fixed 64 MiB host-output-volume reserve is checked immediately before the one-shot marker; below it the runner stops before CUDA. The threshold is based on the adjacent RTX 3080 allocation's tested reserve boundary and is covered by a pure CPU exact-boundary test. It avoids an unsupported larger arbitrary threshold.

The early failures remain disclosed; no seed search, replacement, or output overwrite occurred.
