# Draft GitHub review request — Issue #59

A02 adds a deterministic boundary reproduction for the stale-renewal path that the existing `fc14994` candidate addresses. The reproduction is scoped to frozen controller/cleanup blobs captured from main `b6907899f11b036f2af572e8d4794ebb4b7e5c83`; both normal and optimized runs passed all 21 independent audit checks. It is not a current-main failure claim: main has advanced to `5339abda428b426a7e646dbd3f17f3a62c960584`.

I separately extracted the exact controller and focused test from candidate commit `fc14994f53655da57b9b6573d028ddde1a11b858` and ran `python candidate_test_fc14994.py`: 4/4 passed. The candidate's retained A01 report also records 4/4 focused tests and 15/15 existing wait tests in normal and optimized modes, while keeping full V39 integration on HOLD (Pillow missing for broader suite; no complete planner/executor/game/GUI/input/scorer/cleanup runtime).

Review request: please review whether the renewal rejection is correctly treated as “no cover admitted,” whether the planner remains live only for soft observations and is interrupted on hard invalidation, and whether the event/terminal accounting around coverless recovery is sufficient. Please advise whether the candidate remains applicable to current main and what focused integration check is still required before adoption. No merge is requested by this note.

Evidence: `RESULT.md`, `AUDIT.json`, `CURRENT_MAIN_RECHECK.json`, `CANDIDATE_VALIDATION.md`, and `SHA256SUMS.txt` in this A02 package. GitHub MCP was rate-limited at 2026-10-05 10:05:33 UTC, so this request is saved locally and has not been posted.

GitHub status: `github_add_comment_to_issue` returned `Action completed` and comment ID `5992339018` for Issue #59. A subsequent MCP read-back of issue/comments at 2026-10-05 10:07:49 UTC returned 403 rate limit exceeded, so posting is confirmed by the write receipt but independent public read-back remains unverified. Do not retry through a different identity/API route.
