# Construction record — before formal allocation 01

The four focused construction tests ran on the host (Darwin arm64, CPython 3.14.5) and inside the exact frozen OrbStack image (`python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, Linux/arm64, CPython 3.12.14). Both runs exited 0 with 4/4 tests passing:

- `test_finite_sample_rank`
- `test_shift_flag_suppresses_singleton`
- `test_unattainable_rank_is_full_set_not_clipped`
- `test_wrong_singleton_is_not_counted_as_true_coverage`

The exact container invocation and resource limits are in `COMMANDS.md`. These are construction checks only; the Monte Carlo formal allocation had not run at the time of this record. The auditor and candidate simulator are separate processes; the auditor imports no candidate code.
