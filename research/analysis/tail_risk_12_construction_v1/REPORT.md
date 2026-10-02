# Issue #12 tail-risk construction v1

Status: **FINITE_CONSTRUCTION_PASS / EMPIRICAL_H_UNTESTED**. This is a host-initiated, container-executed mathematical control for the unverified #12 comment on severity-sensitive tail risk. It is not a benchmark result, safety proof, or route selection.

## Source, command, output
Source: `check.py`, local SHA-256 before upload `ebf4847f82c31acc886731a8ddaefad8f2ff005695cbfe2b386e635d888af504`. Image: local `python:3.12-slim`, ID/RepoDigest `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`. No model, GUI, input, GPU, network, or shared formal allocation.

Exact host command (local source filename):
`docker run --rm --network none --read-only --mount type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-github-mcp-main-2\work,target=/work,readonly python:3.12-slim python -B /work/issue12_tail_risk_t0.py`

Exit 0; exact stdout in `result.json`. Published filename `check.py` differs from local filename only; source readback is required to verify content match.

## Result and boundary
With 100 authored observations per arm and worst-10 mean loss: binary A (five loss-1 failures) has 5% failures and tail loss 1/2; binary B (two loss-1 failures) has 2% failures and tail loss 1/5. All 5,151 ordered pairs of possible binary failure counts are monotone in this metric. Changing only B's two failure severities from 1 to 10 makes B's tail loss 2, reversing the binary ranking. The severity 10 is authored, not observed or calibrated. No independent raw-only audit or CI/review is claimed here.

This demonstrates an evaluation-method counterexample, not an actual Agent Interface risk reversal. A future empirical test needs a prospectively frozen severity scale, independent effect/collateral scorer, adequate tail sample, uncertainty accounting, and hard forbidden-effect gates that cannot be averaged away. Prior #12 results remain unchanged.
