# Candidate validation — fc14994

The independently frozen A02 source reproduces the stale sequence rejection on its captured b690 source. The later candidate commit `fc14994f53655da57b9b6573d028ddde1a11b858` was tested separately by extracting its exact controller and regression file into `candidate_controller_fc14994.py` and `candidate_test_fc14994.py`; no production checkout was modified.

Command: `python candidate_test_fc14994.py` with `V39_CONTROLLER_SOURCE` pointing to the extracted controller.

Result: 4/4 PASS (accepted renewal classification, stale-sequence rejection classified as no-cover, unexpected rejection fails closed, and planner remains active for soft observations but interrupts on hard invalidation). This is scoped candidate evidence, not live-game evidence, and does not certify broader cleanup, task-effect, or resource claims.

A first test invocation used an invalid unittest module path and failed before test bodies ran; see `CANDIDATE_TEST_INVOCATION_NOTE.md`. The corrected direct invocation above passed.

GitHub reporting of this finding is pending API availability. At 2026-10-05 10:04:13 UTC, GitHub MCP returned 403 rate limit exceeded. No alternate identity/API route was used.
