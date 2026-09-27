# Issue #3349 — full-runner replay-scope candidate validation (2026-09-20)

This extends PR #3452's contract candidate to a vendored copy of the full current-main runner. It remains an additive candidate; the live main runner and original FAIL are unchanged.

## H/T/D/C/U

- **H:** Applying role-scoped replay to the exact full runner preserves cleanup terminal reuse while preventing retained prelude events from contaminating command waits.
- **T:** Fetched current-main `research/doom/map01_recovery_cover_matched_v2_runner_3202.py` (Git blob SHA `4432a6188b5318dc552f050a26ff9e2a5d32bbf9`, file SHA-256 `4e700b05c60626e73070eb6f5883d9341c8b1374996d45f08e5766fc6cb0f463`). Applied only the replay-scope patch in a vendored candidate. Executed original and candidate against the same eight-case event/queue matrix in `python:3.12-slim` image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, `--network none`; also ran candidate `--help`, compile, and an independent matrix-output verifier.
- **D:** Original exit `1`, failing only `terminal_default_isolated` and `terminal_opt_in`; candidate exit `0`, all eight cases true. Candidate `--help` exit `0`; compile exit `0`; independent verifier `PASS_REPLAY_SCOPE_CANDIDATE_SCOPED`, zero errors. Candidate SHA-256 `7401ecd4fb868aa6960f724711eac043487f1efee7b9f44a376057c2d70962f1`; matrix SHA-256 `50ad79fb4a873bde5cb9dae2a5a02720436c52ba80150f5b6fbe741f36259f6a`; original raw SHA-256 `52ed57d7d34c7d8a836957900ebb17c0c74b676b5da62a58afcdc0b16bc47e05`; candidate raw SHA-256 `dcd6e77dbedec6c54210c6f43d341305c2901d7c6cb4ac094a3cf00b7f8ad932`; independent audit SHA-256 `5741466c65799c822cf0f384898fdabce255148025eb8d8b30b3eb7fbc9423ad`.
- **C:** `PASS_REPLAY_SCOPE_FULLRUNNER_CANDIDATE_SCOPED`. The exact full-runner candidate passes the declared replay-scope contract matrix; the original defect is reproduced.
- **U:** No MAP01/ViZDoom formal allocation was run. This does not establish live recovery efficacy or canonical allocation ownership. The candidate remains separate from the live runner pending review and an independently valid next allocation. Issue #3349 stays open; the prior current-main FAIL remains intact.

Full candidate, matrix, raw outputs, manifest, and verifier are under `research/doom/map01_recovery_event_replay_scope_3202_v3/`.
