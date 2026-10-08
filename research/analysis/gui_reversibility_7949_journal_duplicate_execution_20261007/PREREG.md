# GUI-REVERSIBILITY-7949-JOURNAL-A01

## H / T / D / C / U

**H.** In a disposable SQLite artifact store, comparing independently observed committed state/revision with a journal can distinguish a complete external write from missing, gapped, or inconsistent journal evidence. A recovery proposal bound to a revision must be UNKNOWN on any mismatch. For a complete disjoint-field write, a bounded proposal may restore only the agent-owned field while preserving the external value.

**T.** Six fresh databases: (1) unchanged baseline; (2) complete disjoint external write; (3) complete same-field external write; (4) advanced revision with missing journal row; (5) journal sequence gap; (6) journal/state mismatch. A separate writer subprocess creates each transaction. A read-only observer subprocess reads current state, certificate, and journal. One candidate subprocess consumes only those observations and emits typed decisions/proposals. One independently implemented auditor subprocess reads the SQLite databases read-only and checks observations, journal continuity, candidate cardinality, and bounded proposal contents. No proposal is applied to a database.

**D.** `PASS_JOURNAL_STATE_RECONCILIATION_SCOPED` only if baseline is `NO_CHANGE`; the complete disjoint write is `PROPOSE_COMPENSATION` with proposal to restore `agent_value` to its certificate baseline while preserving the committed `external_value`, and bind the new certificate to the observed revision; same-field, missing-row, sequence-gap, and state-mismatch cases are `UNKNOWN` with no proposal. The auditor must independently query all six DBs, reconstruct all six outcomes, compare observer bytes semantically against DB reads, and reject missing/duplicate/unexpected candidate rows and any wrong action or proposal. Any wrong acceptance or lost/patched external value is FAIL. Missing sources, exit/provenance mismatch, or incomplete audit is STOP/HOLD.

**C.** A single SQLite transaction and locally readable state/journal are a deliberately favorable finite-store contract. An actual application may write outside SQLite, omit related files, have partial commits, or provide dishonest observations. A synthetic transaction does not model a GUI side effect.

**U.** Native macOS standard-library processes only if the predeclared OrbStack image inventory gate is unavailable; no container isolation is then claimed. No GUI, application, model, network, host input, third-party package, privileged action, crash/power-loss durability, malicious database administrator, receipt authenticity, production recovery, or safety claim.

## Runtime gate and one-shot rule

Intake main: `2d227ecf86479cff093123190560bd8d63148ce4`. GitHub Issue #8300 supplies this successor question; predecessor #7949 results and allocations are not changed or rerun. OrbStack `docker info` succeeded, but read-only `docker image ls --no-trunc` failed on an existing content blob with `operation not supported`; no repair, restart, prune, pull, or build was attempted. Therefore this allocation uses the Issue's preregistered native fallback and makes no container claim.

The frozen source/input/gate hashes are in `FREEZE_SHA256SUMS.txt`. Formal process chain (`run_all.py`, then `candidate.py`, then `auditor.py`) is invoked once each after the freeze commit. No retries, replacements, or post-outcome source edits. Outputs are retained under `out/`; only construction/index checks may run before the formal invocation.
