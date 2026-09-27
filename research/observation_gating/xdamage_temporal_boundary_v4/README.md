# XDamage temporal-boundary v4 successor

Successor to #4900's output-path preregistration HOLD. The v3 raw archive and STOP/HOLD remain unchanged.

- Allocation: `xdamage-temporal-boundary-3935-v4-20260928-01`
- Intake main: `763b5db092e0e8a5f6a3f98e9712ba6c9edbcf79`
- Docker image ID: `sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4`
- Exact host output paths are embedded in FREEZE.json. The committed PowerShell launcher reads that frozen manifest, checks its own frozen digest, rejects any noncanonical/pre-existing output path, then starts local Docker directly.
- Run only as `./run_container.ps1 -Mode construction -RepoRoot <local-clone> -SourceCommit <frozen-commit>`; formal is allowed once only after independent construction audit passes.
- Docker uses `--pull=never --network none`; no GitHub Actions/workflow experiment, GPU/model/provider, GUI input, host display, or user data.
- Separate paths and raw outputs for construction and formal; one 6-row construction and one 48-row formal allocation, no retries.
- Scope is XDamage temporal event observation and exact O1 endpoint gating, without action authority.
