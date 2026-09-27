# Issue #4698 — preserved STOP and construction evidence

This is an additive record for [Issue #4698](https://github.com/Unjuno/agent-interface/issues/4698), not formal evidence. The full 3×12 treatment was run before source/FREEZE publication on its exact allocated seeds. It is typed `STOP_PRE_FREEZE_FULL_TREATMENT_CONSUMED`; it must not be relabeled or rerun on those seeds. The independent auditor later checked all 72 checkpoints and requests with zero integrity errors, but that cannot repair the missing pre-run freeze.

Resident request→ack p95 was 200.497 / 109.712 / 111.038 ms against 2,150.798 / 2,012.083 / 1,990.989 ms for respawn; the resident absolute 60 ms hypothesis gate was not met in construction. Adapter-update medians were 2.478 / 2.210 / 2.564 ms, while resident durable-commit medians were 85.475 / 24.218 / 27.123 ms. No formal scientific status is claimed. A fresh matched host-bind vs Docker-native-volume successor is tracked in #4714.

`src/` contains the exact available construction runner, independent auditor, tests, preregistration and failure chronology. `raw/` contains the three retained run JSON files and `AUDIT.json`; `logs/` preserves the compact runner/auditor outputs. The issue body retains the full stop accounting.
