# XDamage temporal-boundary v3 results

- Allocation: `xdamage-temporal-boundary-3935-v3-20260927-01`
- Source commit: `9a27ffd5180ae8c4a77afa872e0f9f2ffb38f0ee` (frozen source, based on main `c1e6f24d259f96b4d4dbf211e83fcdf6b9e0a4dd`)
- Docker image ID: `sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4`
- Execution was local Docker, Linux/WSL2, `--network none`, 1 CPU, 2 GiB memory, no GPU.
- Construction: 1 session / 6 cases; independent disposition `PASS_CONSTRUCTION_PIPELINE`.
- Formal: one invocation, 8 sessions × 6 cases = 48/48; independent disposition `PASS_XDAMAGE_TEMPORAL_BOUNDARY_V3_SCOPED`.
- Formal auditor: `audit_errors=[]`; 9 corruption controls rejected (8 required).
- Protocol unit tests: 7/7 pass.
- Formal ZIP SHA-256: `B220D1C470D3882D0B8F55558ABE6FB066E1C9B23CFD0A524F79802D04B9C824` (`FORMAL_EVIDENCE.zip`).
- Construction ZIP SHA-256: `EA89636BA125BC4324770C676ACCF0B4E8A25C40A8DAC9A391F7B1A7FC2CE44F` (`CONSTRUCTION_EVIDENCE.zip`).

| Case | n | XDamage observed | Endpoint forwarded |
|---|---:|---:|---:|
| QUIET | 8 | 0 | 0 |
| REPAINT_A | 8 | 8 | 0 |
| PERSIST_B | 8 | 8 | 8 |
| ABA_1PX | 8 | 8 | 0 |
| ABA_2X2 | 8 | 8 | 0 |
| ABA_8X8 | 8 | 8 | 0 |

The independent typed negative controls all remain `UNKNOWN` with `action_authority=false`. This is a scoped observation result, not a GUI/action-authority claim. Raw RGB frames, per-case receipts, runner/auditor summaries, corruption-control outputs, and invocation marker are preserved in the ZIP evidence archives.
