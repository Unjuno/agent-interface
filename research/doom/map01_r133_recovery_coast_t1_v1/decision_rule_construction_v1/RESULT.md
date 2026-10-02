# Construction-01 result

Status: `FAIL_AUDIT` (preserved; do not interpret as a passing construction).

- Candidate command: `wsl python3 candidate.py` — exactly one invocation, exit 0.
- Auditor command: `wsl python3 audit.py` — exactly one invocation, exit 1.
- Candidate enumerated 729/729 paired sign vectors. Independent oracle mismatch count: 0.
- Four raw mutation probes were rejected: omitted case, forged tie PASS, duplicate case, and control-status mutation.
- Eleven controls matched their declared outcomes; `identity_hash_malformed` did not. The mutated source-model identity is rejected earlier as `identity_mismatch:model_contract_sha256`, whereas the frozen expected reason was `identity_format:model_contract_sha256`. The complete run is therefore `FAIL_AUDIT`; no repair or rerun was made.
- Raw candidate artifact: `results/construction-01/RAW.json`, SHA-256 `cad232ed057b2c807201baa5077adf995cb60a764155f5a55d58a7385308ade1` (212,931 bytes).
- Audit artifact: `results/construction-01/AUDIT.json`; run receipt: `results/construction-01/RUN.json`.

This was synthetic host-only adjudicator logic checking. No Docker container, Docker Desktop workload, X11, game, model, GUI, input, or shared experiment allocation was used. This result does not validate T1 empirical measures or authorize the live experiment. A corrected reason-precedence/control case, if worth pursuing, must be a separately frozen successor construction and retain these artifacts unchanged.
