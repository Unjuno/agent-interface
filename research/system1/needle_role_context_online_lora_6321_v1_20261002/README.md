# Issue #6354: explicit role context for online Needle LoRA

This additive package tests whether a known role identity and role-gated rank-2 adapter can acquire B online while retaining A. It is a successor to #6321's label-provenance and pre-fit STOPs; those records remain untouched.

Read [PREREGISTRATION.md](PREREGISTRATION.md), [FREEZE.json](FREEZE.json), [CONSTRUCTION_REPORT.md](CONSTRUCTION_REPORT.md), and [RUN_COMMANDS.md](RUN_COMMANDS.md) before any execution. Construction has passed 12/12 tests on the host and in the pinned WSLc CPU container. The frozen synthetic dataset is `construction-01/dataset.json`; SHA-256 and seed/split checks are in the freeze manifest.

No model fitting, CUDA call, optimizer update, formal candidate, or formal audit has run. The exclusive RTX 3080 slot is unassigned. Do not execute the stored candidate command without an exact assignment in #5085. This package makes no adaptation-quality, real-time learning, runtime authority, safety, latency, or product claim.
