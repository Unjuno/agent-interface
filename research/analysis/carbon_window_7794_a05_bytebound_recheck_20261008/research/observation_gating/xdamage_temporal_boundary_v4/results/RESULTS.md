# XDamage temporal-boundary v4 results

- Allocation: `xdamage-temporal-boundary-3935-v4-20260928-01`
- Disposition: `PASS_XDAMAGE_TEMPORAL_BOUNDARY_V4_SCOPED`
- Source commit: `92d7d354b3290e0a4dcd001f02f140bbe781f6bc`, based on frozen intake main `763b5db092e0e8a5f6a3f98e9712ba6c9edbcf79`.
- Docker image: `agent-interface-gtk-preflight:local`, ID `sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4`; local Docker, Linux/WSL2, `--network none`, 1 CPU, 2 GiB, 64 PIDs, no GPU.
- Construction: 1 session, 6/6; `PASS_CONSTRUCTION_PIPELINE`, zero auditor errors.
- Formal: one invocation, 8 sessions × 6 cases = 48/48; independent raw-only auditor `audit_errors=[]`, 9 corruption controls rejected (8 required); 7/7 protocol tests pass.
- Host output roots were frozen in this file set and in Issue #4907 before execution, checked absent, and enforced by the committed launcher: construction `C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-2\scratch\xdamage-v4-construction-01`; formal `C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-2\scratch\xdamage-v4-formal-01`.
- Formal ZIP SHA-256: `3D8B5767ECEA459C20C4F83032C4B31D2E3CF8B70F83C4B3D36877CC9B995531`.
- Construction ZIP SHA-256: `0AEFF4ABF8D3F75126B54545BA622207BBF45F7774F1A73498909378FF1C2AFD`.

| Case | n | XDamage observed | Endpoint forwarded |
|---|---:|---:|---:|
| QUIET | 8 | 0 | 0 |
| REPAINT_A | 8 | 8 | 0 |
| PERSIST_B | 8 | 8 | 8 |
| ABA_1PX | 8 | 8 | 0 |
| ABA_2X2 | 8 | 8 | 0 |
| ABA_8X8 | 8 | 8 | 0 |

All typed negative controls remain `UNKNOWN` with `action_authority=false`. Scope is private core-X11/Xvfb event observation only; no GUI/action-authority claim. The raw archives preserve frames, receipts, invocation marker, summaries, and audit controls. V3's preregistration HOLD and evidence remain unchanged and are not pooled.
