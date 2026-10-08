# Execution receipt — #6561 adversarial mutation T1

- Started: 2026-10-02 06:37:25 UTC
- Frozen repository checkout: `b45f6182a4735046a2be837e2c65c4a36dfb1ad8`
- Frozen main used to create the independent evidence branch: `2a01df459a488f1e09d20c57afc09ddc683420fd`
- Runtime: Windows 10 build 26200, CPython 3.11.9; local CPU only.
- Pre-run source/spec/harness hashes were checked by `run_probe.py` against `PRE_RUN_SHA256SUMS`.
- Candidate invocation: `python -B .\run_probe.py .\results\t1-20261002-01` — exit 0; generated 5 finite packets; no prior output path existed.
- Target raw auditor: five separate local CPython subprocesses, one per packet. Raw stdout/stderr and exit codes are retained in `results/t1-20261002-01/target_auditor_outcomes.json`.
- Outcome: the valid control passed, and all four predeclared corruptions also exited 0 with `PASS_RAW_AUDIT cases=6`. Raw inputs are retained in `raw_packets.json`.
- Independent post-run auditor attempt: `python -B .\audit_probe.py .\results\t1-20261002-01` was included in a PowerShell command chain that did not preserve that process's exit code or stdout/stderr separately. A subsequent read-only check found no `RESULT.json`; therefore classify the independent post-run audit as `STOP_POSTRUN_AUDIT_NOT_RETAINED`. It was not retried.
- Disposition: raw target-auditor behavior meets the preregistered failure condition (`FAIL_TARGET_AUDITOR_ACCEPTS_MUTATION`); the stricter independent package audit is STOP/unverified. Keep both outcomes distinct.
- Scope: host-only contract-packet boundary test against the immutable draft-PR snapshot. No WSLc/container, GPU/CUDA, game, GUI, model, or user input. No live runtime implication. Candidate/auditor retries: 0; mutation cases are the single preregistered sweep.
