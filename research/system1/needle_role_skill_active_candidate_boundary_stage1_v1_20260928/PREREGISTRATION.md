# Issue #4986 Stage 1 — atomic candidate publication boundary

This allocation is frozen before execution. Stage 0 remains a scoped construction result and is not re-run. No seeds, fit steps, or model calls are involved.

## H / T / D / C / U

**H.** Publishing a role-skill candidate only after exact validation prevents all shadow readers from seeing an unvalidated package; publishing at validation start (unsafe diagnostic arm only) exposes it during the validation delay.

**T.** Allocation `needle-role-skill-active-candidate-boundary-stage1-v1-20260928-01`, Issue #4986. Frozen against branch base main `1a9cbcc3552089d3c791518e8f6e85e3e415f93d`, after Stage-0 merge `ae06482dd00b9756546620217c9b92f12ca672b3`. Branch `research/needle-role-skill-active-boundary-stage1-v1-20260928`; additive path `research/system1/needle_role_skill_active_candidate_boundary_stage1_v1_20260928/`.

The exact input is the #3890 seed-3788 inert `skill.json` (SHA-256 `2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a`) and the frozen Stage-0 raw file from which the exact generation-3789 candidate bytes are derived (SHA-256 `84c39bfa134d6b788423378faedb763524f409de4eedfa09ca8c983859663250`). Compare two arms: (1) `PUBLISH_AT_VALIDATION_START`, diagnostic only, exposes a complete candidate before its validation receipt exists; (2) `PUBLISH_AFTER_VALIDATION`, candidate path, keeps old bytes ACTIVE until schema/generation/scope/digest checks complete and receipt is bound.

Each arm uses eight concurrent read-only threads per barrier wave, eight fixed waves, 64 queries. Waves 0–3 occur while validation is pending, with a fixed 10 ms delay after each wave (40 ms total). Wave 4 releases eight readers and the writer on one nine-party barrier; the writer performs the safe publication at that boundary. Waves 5–7 follow publication. Total: 128 shadow queries. No query dispatches an action.

**D.** `PASS_ATOMIC_SKILL_PUBLICATION_SCOPED` only if exactly 128 query IDs are accounted once; each observed snapshot is a complete known package with valid content digest and matching generation; the unsafe diagnostic exposes the candidate to exactly 32 prevalidation reads; the safe arm exposes it to zero prevalidation reads; the boundary wave contains only complete old/new snapshots; all safe post-boundary reads see the candidate; dispatch count is zero; and an independent raw-only auditor returns zero errors with all six corruption controls rejected. Any unmet gate is retained as FAIL/STOP; no retries or post-result threshold changes.

**C.** One local Docker Desktop Engine 28.5.1 linux/amd64 host, pinned cached Python image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, network disabled, read-only root/source, 1 CPU, 512 MiB, 64 PIDs. Hand-authored inert synthetic package. No model, training, optimizer, GUI, provider, user data, or action authority.

**U.** This does not prove general filesystem/process crash consistency, cross-process or cross-host memory ordering, real Needle/Astra adaptation, task effects, performance, production safety, or product readiness. The unsafe diagnostic arm is not a candidate design.

## Frozen input identities

- `runner.py` SHA-256 `02fc12d6fbf0bff325526b155c702e0f238f2ff73171b5cc45d3ad0ebca8b5b7`
- `audit.py` SHA-256 `deedea27a080522d587a5c7733a49562da9aed9b0099ba80649ac61b0536d962`
- `test_controls.py` SHA-256 `ca3f7d04cb95659fe72231b909d2d247decbd03f528c384ee6579fe313cdbda7`
- Exact commands and container mount roles are frozen in `FREEZE.json`.

No Docker runner/auditor invocation has occurred at the time this preregistration was committed. The allocation is one runner invocation, one separate auditor invocation, no retry.
