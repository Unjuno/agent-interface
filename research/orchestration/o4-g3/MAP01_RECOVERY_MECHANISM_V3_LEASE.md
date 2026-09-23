# Formal live-experiment lease — MAP01 recovery mechanism v3

Allocation: `map01-recovery-cover-mechanism-live-v3-01`  
Question: causal bounded-recovery mechanism under fixed 600 ms simulated planner delay  
Lease holder: `O4/G3`  
Immutable construction base: `ff2bbb5e200e2bf8ee2295ad97ca9dd0f158a371`

Status before launch: **LEASED; formal outcome not yet consumed.**

The lease authorizes exactly one workflow-path-global first formal outcome for `.github/workflows/map01-recovery-cover-mechanism-live-v3-01.yml`. It does not authorize the older `map01-recovery-cover-matched-live-v2-01` model-efficacy allocation.

The lease expires immediately when the canonical workflow run reaches its first formal outcome, whether PASS, HOLD, FAIL, environment failure, or audit failure. Same-allocation retry requires a new version and a new lease.

At lease acquisition, the repository Actions API reported zero in-progress runs and no existing commit/branch for this allocation identity was found. The workflow-path-global owner remains the executable fail-closed enforcement mechanism; this file is the research-coordination record.
