# Issue #5156 Allocation 07 — resource coordination STOP

## H / T / D / C / U

- **H:** For explicit per-key client release, owner-thread `KeyRelease` to
  `XSync` timing may be identity-bound and nested inside a caller bracket. No
  scientific observation was made for this hypothesis in Allocation 07.
- **T:** The preregistration required an exact resource grant and clean start
  gate before one private-Xvfb fixture candidate and one independent auditor.
- **D:** **STOP_RESOURCE_COORDINATION_BEFORE_CANDIDATE.** Read-only inventory
  found four nonterminal `Created` containers with unresolved ownership/release
  state. Candidate=0, auditor=0, container starts=0, image inspections=0.
  `scientific_result=NOT_EVALUATED`; do not interpret as PASS or FAIL and do not
  retry or reuse this allocation.
- **C:** The gate refused to disturb unrelated containers without explicit
  owner/release evidence. Host-only construction tests are not formal X11
  evidence.
- **U:** No X11/Xvfb, GUI, input, physical-key, release-timing, task-effect,
  safety, or production conclusion. A fresh successor requires separate
  authorization and resource coordination; this package supplies neither.

Original `STOP.json` and `START_GATE_INVENTORY.json` remain unchanged. See
`ARCHIVAL_QUALIFICATION.md`.
