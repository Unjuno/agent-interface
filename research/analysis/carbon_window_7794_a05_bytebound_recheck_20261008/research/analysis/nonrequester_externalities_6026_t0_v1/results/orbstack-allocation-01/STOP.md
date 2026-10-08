# OrbStack allocation-01 start-gate STOP

- Allocation: `NONREQUESTER-EXTERNALITIES-6026-T0-20261001-01` (reserved 2026-10-01 16:15–16:30 UTC on #5085).
- Gate checked: 2026-10-01 16:15:26–16:16:01 UTC.
- Outcome: `STOP_PREFLIGHT_RUNNING_UNOWNED_CONTAINER_AND_STALE_MAIN`; candidate=0, auditor=0, retries=0. No candidate or auditor container was created or started. No unowned container was inspected beyond the inventory or modified.

## Evidence

- The latest #5085 comments still showed this owner-bound allocation in its reserved window and no later cancellation or overlapping allocation. #6026 was OPEN. PR #6066 was Draft at head `a26ba40d8ae2214519d91b59da1d436171464167`.
- `docker --context orbstack ps --filter status=running --no-trunc` showed an unrelated live container: ID `af2a0db6c5aa6125f3e99f28c7917d2cb28ddd4b4504b60143ae78661ef5c3e6`, name `unjuno-native-ci-6092`, image `python:3.12-slim`, command `sleep infinity`, running for about two hours. It is not owned by this allocation. The shared queue's preceding #6000 and #6028 allocations had also STOPped on this same container. It was left untouched.
- `origin/main` at the gate was `2106f20d61e4ef80cfcdbb2b694bbe10a07b454d`, while this branch was `a26ba40d8ae2214519d91b59da1d436171464167`; `origin/main` was not an ancestor of the branch. This independently failed the frozen-main gate.
- The four frozen method inputs still matched their prior SHA-256 values:
  - `fixture.json`: `7f310012606f3d6085254ed43604dfbbde6033d08b921d9342c2a8d311dc003a`
  - `candidate.py`: `336f82b82d920a70c7272db8064d2b4a94babbd2fda9780daabddc5be52fdb33`
  - `audit.py`: `c9435a477805e445c14dc1dce090c9991425dfd3378e6f29c8077c00d2a93ce0`
  - `test_method.py`: `a29f9319893a72b2a84c6846ccb2d97a562ebdd9acb168e3806ef95746b4c7c2`
- The pinned image was present and identified as `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `linux/arm64`.
- Both allocation-specific candidate and auditor container names were absent. Their absence does not override the running-container and main-freshness failures.

The allocation is consumed and released. Do not retry it. A future container attempt requires a new queue allocation, a clear shared OrbStack inventory, and a fresh branch based on the exact then-current main. The already-passing host-method result remains separately labeled host-only and is not upgraded by this STOP.
