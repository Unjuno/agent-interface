# Issue #6515 T0 preregistration — allocation 02

Allocation: `PLANNER-BLIND-CREDENTIAL-ENTRY-6515-T0-HOSTCPU-20261003-02`  
Base: `2ebde9d05592a3a8f866fafcb4cbef888f53d199`  
Branch: `research/planner-blind-credential-entry-6515-t0-20261003`  
Package: `research/analysis/planner_blind_credential_entry_6515_t0_v1/`  
Raw output: `results/formal_02/candidate_raw.json`  
Audit output: `results/formal_02/audit_result.json`

This is a new allocation. Allocation 01 stopped before any formal process because `main` advanced between freeze and launch; its freeze and stop record remain preserved. No result from allocation 01 is carried forward.

The H/T/D/C/U, 15-case × 5-policy design (75 rows), semantics, and limitations are exactly those in `PREREGISTRATION.md`; that file and all candidate/fixture/auditor/test bytes are reused unchanged. This allocation's source hashes are recorded in `FREEZE_A02.json`. It compares two typing baselines, a conservative transcription of published agent-browser provider documentation, a synthetic request-bound broker, and no-automation/manual fallback. It does not execute or test the actual provider.

Construction gate: `python3 -W error::ResourceWarning -B -m unittest -v test_t0` (7/7) passed before allocation 01 froze; source hashes verify that those exact bytes remain in use. The previous publication explicitly records this construction pass.

Candidate, once: `python3 -B candidate.py fixture.json results/formal_02/candidate_raw.json`  
Auditor, once and only after candidate exit 0: `python3 -B audit.py fixture.json results/formal_02/candidate_raw.json results/formal_02/audit_result.json`

Runtime and restrictions are inherited unchanged from the original preregistration: host CPython stdlib only; no secrets, accounts, network, browser, GUI, user or OS input. WSLc remains prohibited by #5085 and shared Docker/OrbStack has no assigned ownership. Stop before candidate if `main` advances, any source hash differs, or either output path exists. Retries are zero.
