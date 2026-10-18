# Issue #8406 A02 — retained-raw audit-only successor

## Scope

A01's candidate executed once and its immutable raw output is retained at `../episodic_memory_schedule_8406_t0_a01_20261008/formal_01/RAW.json`. A01's auditor then stopped before producing an audit because its hostile-control code indexed a keyed schedule object as a list. This successor independently reconstructs and audits those exact retained bytes. It does not run or replace the candidate, does not change A01's `STOP`, and does not claim model-facing schedule sensitivity.

## Frozen inputs and method

- Parent #7418 fixture path/hash: `../exception_preserving_skill_7418_t0_20261004/fixture.json`, SHA-256 `1c8b74dfdd8ec7c5a5950133709ae95e40cc687edb12ac128d66f696c79e54fb`.
- A01 candidate raw path/hash: `../episodic_memory_schedule_8406_t0_a01_20261008/formal_01/RAW.json`, SHA-256 `2c79a10fa6530d74ac17ea9c67816b9517c63235a4cd32fcf70a2d463d4d9f70`.
- Independently reconstruct twelve immutable source episodes, source-content hashes, four keyed schedule arms, updates and fixed-prefix query visibility from the parent fixture and its applicability oracle. Compare the complete canonical object to retained raw bytes parsed as JSON.
- Require update counts 0/12/3/1 and 16 query rows per arm.
- Apply five actual hostile mutations to deep copies: forged source ID, omit rare exception, add safe conclusion to unresolved conflict, mutate source digest, and misalign batch checkpoint. Each must differ from the independently reconstructed object.
- No model, network, GUI, action, user data, candidate invocation or claim about consolidation quality/cadence effects.

## Gate and custody

Disposition is `PASS_RETAINED_RAW_AUDIT_SCOPED` only when hashes, full reconstruction, counts and all five controls pass. Any discrepancy is `FAIL_RETAINED_RAW_AUDIT`; no retry. A01 remains `STOP_AUDITOR_KEYERROR_SCHEDULE_SHAPE` irrespective of this audit-only successor. This host-only standard-library audit makes no container isolation claim; the package does not need a container runtime or external dependency.

Frozen source commit and one-shot command are recorded in `FREEZE.json`. Formal output is exclusive-created at `formal_01/AUDIT.json`; invocation receipt is `formal_01/RUN.json`.
