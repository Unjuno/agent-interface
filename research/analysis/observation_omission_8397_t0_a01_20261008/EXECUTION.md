# Execution record — Issue #8397 T0 A01

- Base main at freeze: `2f36f501f11931e052dbc3fb0000a9200bff7f50`.
- Branch: `research/observation-omission-8397-t0-a01-20261008`.
- Host boundary: attached Windows workspace, PowerShell 7.6.6, CPython 3.12.10.
- No WSL/WSLc, Docker/OrbStack, GUI, model, game, OS input, network, or GPU
  operation was used.
- Candidate and auditor use only the Python standard library.
- Construction command before freeze: `python -B -m unittest -v test_contract.py`.
  Outcome: 7 tests passed in 0.003 s, exit 0. This includes five independent
  mutations; each was rejected by the raw auditor.
- Freeze identities are in `FREEZE.json`. All frozen SHA-256 values were
  rechecked immediately before candidate execution; all matched.

## Formal invocations

1. `python -B candidate.py fixture.json results/candidate_raw.json`
   - invocation count: 1; retry count: 0
   - exit: 0
   - stdout: `{"scenarios": 5, "arms": 10, "output": "results\\candidate_raw.json"}`
   - stderr: empty
2. `python -B auditor.py fixture.json results/candidate_raw.json results/audit.json`
   - invocation count: 1; retry count: 0
   - exit: 0
   - stdout: `{"disposition": "PASS_METHOD_SCOPED", "problems": 0, "checks": {"early_omission_preserves_effect_and_reduces_cost": true, "transition_omission_exposes_regret": true, "completion_suppresses_post_completion_observation": true, "captured_undelivered_is_not_visible": true, "mandatory_safety_bypasses_omission": true}}`
   - stderr: empty

Raw candidate, independent audit, stdout/stderr captures, frozen source, and
input are retained in this directory. Their digests appear in
`SHA256SUMS.txt`. No process/container was left running by this package.
