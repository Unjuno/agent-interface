# Issue #3349 — retained-event replay scope candidate matrix (2026-09-20)

Additive candidate evidence only. The existing current-main FAIL remains unchanged; this does not validate or authorize a MAP01 formal allocation.

## H/T/D/C/U

- **H:** Separating queue-bound command waits from explicit terminal-cleanup replay prevents stale prelude accepted/rejected events from satisfying later waits, while preserving exact terminal cleanup reuse and rejecting ambiguous duplicate terminals.
- **T:** Frozen current-main source `research/doom/map01_recovery_cover_matched_v2_runner_3202.py`, Git blob SHA `4432a6188b5318dc552f050a26ff9e2a5d32bbf9`. Applied an additive local candidate change: `wait(..., replay=False)` is queue-bound by default; only fallback terminal cleanup opts into replay; opt-in replay requires exactly one retained match. Ran an 8-case matrix on both original and candidate in `python:3.12-slim` (`sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`) with `--network none`.
- **D:** Original runner failed exactly `terminal_default_isolated` and `terminal_opt_in`; candidate passed all 8 cases. Cases: terminal replay only on opt-in; default terminal wait isolation; stale accepted/rejected rows cannot satisfy submit; duplicate terminal rejected; wrong terminal ID rejected; queued fallback accepted; stale retained and queued prelude rows do not block a valid queued fallback. Independent verifier: `PASS_REPLAY_SCOPE_CANDIDATE_SCOPED`, 8 cases, no errors. Original source file SHA-256 `4e700b05c60626e73070eb6f5883d9341c8b1374996d45f08e5766fc6cb0f463`; candidate SHA-256 `7401ecd4fb868aa6960f724711eac043487f1efee7b9f44a376057c2d70962f1`; matrix SHA-256 `50ad79fb4a873bde5cb9dae2a5a02720436c52ba80150f5b6fbe741f36259f6a`; independent audit SHA-256 `5741466c65799c822cf0f384898fdabce255148025eb8d8b30b3eb7fbc9423ad`.
- **C:** `PASS_REPLAY_SCOPE_CANDIDATE_SCOPED`. The original replay-scope defect is independently reproduced, and the candidate contract passes its bounded matrix. The candidate is not merged into the live formal runner by this result.
- **U:** This validates `JsonSession.wait` role semantics only. No real MAP01 allocation, ViZDoom efficacy, cleanup-runtime integration, or formal allocation ownership was exercised. Keep #3349 open; source review and separate allocation authorization/evidence remain required.

Candidate source, matrix, raw outputs, and independent verifier are under `research/doom/map01_recovery_event_replay_scope_3202_v2/`.
