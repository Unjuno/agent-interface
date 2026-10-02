# Issue #6515 T0 preregistration — allocation 03

Allocation: `PLANNER-BLIND-CREDENTIAL-ENTRY-6515-T0-HOSTCPU-20261003-03`  
Base: `e7f11cdc2cdee42b0f745add6c4a93fc641abe6d`  
Branch: `research/planner-blind-credential-entry-6515-t0-20261003`  
Package: `research/analysis/planner_blind_credential_entry_6515_t0_v1/`  
Raw output: `results/formal_03/candidate_raw.json`  
Audit output: `results/formal_03/audit_result.json`

Allocations 01 and 02 both stopped before candidate invocation because `main` advanced after freeze. Their records and freezes remain preserved. This is a new allocation, not a retry. The experiment and H/T/D/C/U are as defined in `PREREGISTRATION.md`: 15 synthetic cases × 5 policy profiles = 75 rows, comparing typing baselines, a documentation-only provider profile, a synthetic request-bound broker, and manual/no automation. The provider itself is not executed. Source bytes are reused without modification; their digests are in `FREEZE_A03.json`.

Candidate once: `python3 -B candidate.py fixture.json results/formal_03/candidate_raw.json`  
Auditor once after candidate exit 0: `python3 -B audit.py fixture.json results/formal_03/candidate_raw.json results/formal_03/audit_result.json`

The host-CPU-only restrictions in the original preregistration apply. No secrets, accounts, browser, network, GUI, user or OS input. WSLc calls remain prohibited by #5085; shared Docker/OrbStack has no assigned owner. Prelaunch requires exact base equality to this freeze, unchanged source hashes, and absent result paths. Zero retries. This preregistration is valid only for this pinned base; if it advances before launch, stop and defer new allocation until the repository base is stable.
