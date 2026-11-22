# Issue #57 current-main public MCP/Calc composition R03

## Frozen conditions

- Main revision: `066d70435fe19d0dc2690bc01a114e0912b20f87`.
- Host: Windows 11; CPython 3.11.9.
- Test selector: `ProviderToPublicMcpCompositionTests.test_fake_app_server_generation_is_recorded_through_calc_profile_and_score` in `research/integration/standard_mcp_task_ledger_57_v1/test_mcp_endpoint_composition.py`.
- Run once in a fresh normal process and once in a fresh optimized (`-O`) process.
- Each run passes only if the selector reports exactly one test and exits 0. Preserve failures and skips as outcomes.
- This is the repository's deterministic Fake App Server/Fake X composition test. It must use temporary files and fake ownership; it does not call a real provider, real GUI, Docker, WSL/WSLc, or an external allocation.
- `AGENT_INTERFACE_RETAIN_APP_SERVER_CALC_EVIDENCE` was unset before the run.

## Pinned source hashes

| File | SHA-256 |
|---|---|
| `research/integration/standard_mcp_task_ledger_57_v1/test_mcp_endpoint_composition.py` | `446bb7baba9b2bf9e44a913d72bdc911cf6427fb6f20d9bb46cccb3615e519d5` |
| `runtime/guarded_x11_v1/calc_task_artifact_v1.py` | `9538aa01b834c1d9a80a097ae99f2053131b7c5187068aa670355adeb247d81e` |
| `runtime/cli_v1/mcp_server.py` | `a3e542b26dc65b341b758cb7c8b7e59576dbe4110df92eeb2174882056ad22c5` |
| `runtime/guarded_x11_v1/test_calc_task_artifact_v1.py` | `d2e4573e0761df31603354b22ce7c5e07d6b7a6cf0f0c0448710919c94304855` |
| `runtime/cli_v1/test_mcp_owned_process.py` | `046e2c71a6d1d7ca1133f8fed4b43bf48435140d7e8a99ccd802ca8bd6d49e63` |

This recertifies one existing synthetic composition selector against the then-current main source. It cannot qualify live provider usage, standard-caller task success, recovery reliability, or efficiency.
