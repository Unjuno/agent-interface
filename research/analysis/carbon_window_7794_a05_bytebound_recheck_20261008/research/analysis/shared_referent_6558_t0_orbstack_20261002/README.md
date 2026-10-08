# Issue #6558 — purpose-bound shared referent T0 (OrbStack)

Status: allocation 02 `PASS_METHOD_SCOPED`; allocation 01 preserved as a terminal Docker-launch STOP. This T0 tests only whether a synthetic protocol can reject or re-ground a previously acknowledged referent after selected GUI source-generation changes. It does not represent participant comprehension, GUI behavior, runtime safety, or product benefit.

## H / T / D / C / U

- **H:** On this authored two-object fixture, a source-generation-bound restatement will safely identify changed referents or return UNKNOWN, catching seeded target mismatches while preserving unchanged/zoom-only references, with no authority expansion. If it cannot outperform stale coordinates / machine rebinding / initial clarification on seeded changes without excessive re-asks, reject the added protocol for this fixture.
- **T:** Nine frozen cases; four arms: stale coordinate, fresh machine binding to the previously selected node, initial clarification without later re-grounding, and scoped restatement/re-grounding. Cases cover stable clear, initial ambiguity, sort with reused node, virtualized row reuse, zoom-only benign transform, app update after acknowledgment, missing distinguishing property, stale response generation, and attention-only cue. Candidate sees public fixture only. Auditor separately reads the hidden intended-object oracle and candidate raw. Candidate and auditor each run once in separate offline OrbStack containers, image pinned by digest, read-only sources, distinct output mounts. No GUI/model/participant/input/API call.
- **D:** `PASS_METHOD_SCOPED` only if the independent auditor reconstructs all 9 rows and all arms, the scoped arm correctly re-grounds all valid referent-changing cases, fails closed on missing/stale/ambiguous evidence, incurs no ask for stable/zoom-only cases, and no arm turns attention into authority; four mutation controls must be rejected. Any mismatch is `FAIL_METHOD`; infrastructure failure before candidate is `STOP` and no retry.
- **C:** Authored finite truth, object properties, event classes, and user responses may be easier to resolve than real shared-desktop references. Machine node identity may be more or less reliable than the modeled reused-node cases.
- **U:** No participant understanding, actual GUI source generation, application semantics, OS input, effect, authority system, real confirmation cost, or human-benefit claim. No universal GUI guarantee or external novelty claim.

## Frozen protocol

See `RUN_PROTOCOL.md`, `FREEZE.json`, and `formal_02_20261002/PREREGISTRATION.md`. Allocation 01's invalid Docker mount was recorded as STOP and not retried. Allocation 02's candidate input excluded the oracle file; the auditor ran in another clean container and independently passed. The construction suite is a pre-freeze check and is not formal candidate/auditor evidence.

## Reproduction

Commands, exact image identity, container IDs, stdout, output hashes and cleanup are recorded under `formal_01_20261002/` and `formal_02_20261002/`. The top-level `REPORT.md` is the index entry; each allocation report preserves its own outcome.
