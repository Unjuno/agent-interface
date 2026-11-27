Prepared at 2026-10-24T13:58:52.3800856+00:00 before the one S05 WSLc session. Baseline Git commit: 2166707229958e095d472c80e160c26449de7a29. SOURCE_FREEZE.json binds all current runtime/**/*.py plus the attempt's probe, auditor, runner and plan. inputs/DEPENDENCIES.json hashes the exact mounted dependency files. HARNESS-SHA256SUMS.json binds the C# harness, project, runner, conditions, plan and dependency manifest. No S05 WSLc session, image pull or container run had started when this record was written.

Session: agent-interface-wslc-fake-x-s05-55ad2e4cffa74252a7a63d97a3134d4c
Storage: D:\CodexData\Temp\agent-interface-wslc-fake-x-s05-55ad2e4cffa74252a7a63d97a3134d4c (absent at pre-registration)
Container: agent-interface-wslc-fake-x-s05-55ad2e4cffa74252a7a63d97a3134d4c-probe
Image: python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f

A saved pre-run freeze was preserved as SOURCE_FREEZE-PRE-RUN-01.json. After adding bytewise dependency verification in runner.py and the condition record, the final SOURCE_FREEZE.json was regenerated. No container or WSLc session was started between freezes. The final hashes in HARNESS-SHA256SUMS.json are authoritative for S05.

Final source freeze SHA-256: 4a204b0a131c5543c068c1c5105bdc70784171a470ad29f14b8fe0b800998e05 (247 source files). Preflight captured at 2026-10-24T14:00:49.3595597+00:00: WSLc wslc 3.0.3.0; main/source both 2166707229958e095d472c80e160c26449de7a29; output folder empty; exact generated storage path absent. No global WSLc inventory and no Docker command were used.
