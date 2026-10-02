# Formal T0 start gate — `HOLD_RESOURCE_BEFORE_FORMAL_START`

At 2026-10-02 11:20:12 UTC, no candidate, independent auditor, or formal container had started (0/0/0; retries 0). This is an unassigned resource hold, not a scientific result, method failure, or allocation execution.

The required WSLc runtime is unavailable on this macOS arm64 host. Docker reports OrbStack 29.4.0/aarch64, but its shared engine has two running containers (`unjuno-native-ci-6092`, `cans-of14-n64-dt0.0005`). Five separate OrbStack machines are also running for other work (full inventory is in `RUN_RECORD.json`). No owner release or exclusive assignment is present. A stopped OrbStack machine associated with another issue was not reused. All checks were read-only; no foreign runtime was inspected internally or modified.

The exact protocol, local-only construction defect/correction, and formal stopping rule are in [PREREGISTRATION.md](PREREGISTRATION.md) and [CONSTRUCTION_LOG.md](CONSTRUCTION_LOG.md). The local suite is 4/4 after the pre-freeze construction repair; host CLI smoke is not formal and its raw is not promoted. Formal execution may start only after an exact named exclusive CPU/container slot is assigned, the chosen engine inventory is known empty/isolated, and current main/source/image identities are refrozen. No retry or changed allocation is implied.
