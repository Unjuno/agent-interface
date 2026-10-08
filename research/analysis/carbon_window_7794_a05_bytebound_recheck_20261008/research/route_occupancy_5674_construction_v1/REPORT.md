# Issue #5674 — route-induced occupancy T1 construction

Status: **METHOD_PASS_SCOPED / H_UNTESTED**. This is a deliberately constructed two-state Markov example, not a GUI, model, controller, safety, or real route result.

## Frozen source and execution
- Source: `check.py`, host SHA-256 `2d2af549cc32dd58492b85773b57b736262a2e7c6be90b54ea27bb428855864a` before upload.
- Image: local `python:3.12-slim`, image ID / RepoDigest `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- Command (PowerShell host; `work` was the isolated source directory):
  `docker run --rm --network none --read-only --mount type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-github-mcp-main-2\work,target=/work,readonly python:3.12-slim python -B /work/issue5674_occupancy_t1.py`
- Exit: 0. Exact stdout: `result.json`. No network, GPU, model, or GUI call; no shared formal allocation.
- GitHub publication is additive under this path. The original local filename differs from the published `check.py`; check source readback is required before treating the hash as matching the publication.

## Construction and gates
Both routes start in `fresh`, have equal horizon 3 and state-specific burden 1 in `recovery`, 0 in `fresh`. A uses fresh→recovery 1/10 and recovery→recovery 1/2. B uses 2/5 and 3/4. Exhaustive enumeration of eight three-step paths independently agrees with forward recurrence. Result: A recovery probability 39/250; B 589/1000. Reusing A's occupancy to estimate B's burden gives 39/250 versus direct B 589/1000, discrepancy 433/1000. Equal-kernel null control gives zero discrepancy. Row normalization, nonnegative probabilities and total mass are asserted.

This establishes only that the proposed audit can distinguish a constructed occupancy shift from its null. It does **not** establish H in an actual desktop task. #5674 T0 found no eligible retained transition cohort. T2 remains unallocated; direct task-level intention-to-treat correctness and independent effect/release scoring remain mandatory.
