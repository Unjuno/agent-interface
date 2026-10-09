# Issue #8574 T0 A01 — perspective-guided review of cross-invariant contracts

## H/T/D/C/U

**H.** On a small, pre-frozen multi-invariant contract set, a perspective-guided reading procedure may detect at least one source-supported cross-invariant omission missed by both an ordinary checklist and blinded free-form decomposition, without adding unsupported requirements or resolving genuine ambiguity as fact.

**T.** Sixteen authored low-risk contracts: four low-interaction controls and twelve multi-invariant cases. Six reviewers are assigned in two isolated waves (two per arm); each reviewer sees all cases once. The second reviewer in each arm receives the reverse case order to counterbalance order. Freeze exact source/verification pairs, gold source-clause and interaction inventory, blind case IDs/order, three arm procedures, output schema, and adjudication rubric before review. Each arm reviews every same case once, in an isolated context. Reviewer type: independent Codex subagents (same configured model family; findings are agent-review evidence only). No GUI, live user data, tool action, runtime, or external model API. After reviews, a separate adjudicator receives anonymized findings and the source/verification pairs without arm labels or hidden mutation identity. A raw-only audit independently checks assignments, case coverage, gold classifications, adjudicated findings, control behavior, and counts.

**D.** PASS_METHOD_SCOPED only if at least one perspective reviewer finds a gold cross-invariant omission found by zero checklist reviewers and zero free-form reviewers; controls receive no unsupported additions; ambiguities remain `AMBIGUOUS_SOURCE`/HOLD; and the raw-only auditor reconstructs all assignments and counts. NO_INCREMENTAL_VALUE_SCOPED if no qualifying incremental cross-invariant finding appears. FAIL_METHOD if any arm invents a source requirement as definite, misses a preregistered explicit control obligation while claiming full coverage, or sees hidden labels. HOLD if blind separation, adjudication, or reviewer independence fails.

**C.** An ordinary checklist or free-form decomposition may catch the same obligations; the perspective lenses may be redundant.

**U.** Synthetic authored contracts and independent Codex contexts do not estimate human reviewer performance, real omission prevalence, production correctness, or GUI safety. Reviewers share a model family, so independence is procedural, not statistical or model-family independence.

## Frozen design

- Base main: `c995efeca4349353e1f5e13cd1b8aba29088b632`.
- Allocation: `8574-T0-A01-20261009`.
- Two independent reviewers per arm; all 16 blinded pairs per reviewer; no retries. For each arm, reviewer A receives `blind_packet_order_a.json` and reviewer B receives `blind_packet_order_b.json`.
- Source pack: `blind_packet.json`; gold is held separately until reviews close. Case IDs and order are seeded and do not encode strata or defect class.
- Result criteria and categories are in `README.md`/`AUDIT_PROTOCOL.md`; package files and raw responses are hashed prospectively.
