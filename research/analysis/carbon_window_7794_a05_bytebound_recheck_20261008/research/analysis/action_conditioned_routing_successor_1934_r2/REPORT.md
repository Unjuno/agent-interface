# Issue #1934 successor r2 — action-conditioned attention routing

Reconstructed from current `main` after PR #2059 became non-mergeable. The prior branch and evidence remain unchanged.

## H/T/D/C/U

- **H:** A task-conditioned router can select inspection regions relevant to the current intent while preserving raw evidence and never granting action authority.
- **T:** Freeze save, move, unknown, and malformed intents; compare each route with an explicit finite oracle.
- **D:** `experiment.py`, route ledger, UNKNOWN handling, raw-retention flag, authority counter, and SHA-256 digest.
- **C:** Save and move select disjoint intent-appropriate regions; unknown/malformed inputs fail closed; raw evidence remains retained and authority remains false.
- **U:** Automatic intent interpretation, model usefulness, GUI correctness, cue overload, token/latency effects, and runtime transfer remain unknown.
- **STOP:** One finite standard-library fixture; no model, GUI, network, runtime, or user input.

## Result

Command: `python experiment.py`

- Save routes to status/dialog/button.
- Move routes to position/obstacle/collision.
- Unknown and malformed intents return UNKNOWN with no regions.
- Raw evidence retained for all four cases; authority events are 0.
- Digest: `9d061135b76539b186ba7da43cac50ae269f99b619efb100e52c6a294b50a70c`.

**Decision: PASS_ACTION_CONDITIONED_ROUTING_SAFETY_SCOPED.**

This verifies only finite routing safety and fail-closed semantics.
