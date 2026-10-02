# FORMAL STOP — Issue #6210 T0 allocation 01

- Allocation: `SCHEMA-EQUIVALENCE-6210-T0-20261002-01`
- Planned branch: `research/schema-equivalence-6210-t0-20261002`
- Planned result path: `research/analysis/schema_equivalence_6210_t0_20261002/`
- Frozen base: `2a01df459a488f1e09d20c57afc09ddc683420fd`
- Stop code: `STOP_WSLc_UNAVAILABLE_NO_AUTHORIZED_RUNTIME_SUBSTITUTE`

## Pre-start state

- WSLc executable lookup: `command -v wslc` returned no path on macOS.
- Docker CLI is installed, but the finite T0 does not require an Engine API,
  Compose, unsupported isolation/resource controls, or GUI-specific behavior.
- Candidate invocation: **0**; independent auditor invocation: **0**;
  container invocation: **0**.
- No candidate/raw/audit output was created. No retry, engine substitution,
  or resource request was made.

This is an infrastructure STOP before the scientific test. It is neither a
scientific FAIL nor evidence for or against schema sensitivity. Preserve this
record unchanged; a future run needs a newly frozen authorized WSLc allocation
and successor evidence rather than retroactively converting this STOP.
