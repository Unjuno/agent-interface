# #5352 effect-qualified hysteresis discriminator (T15 proposal)

Status: preparation only. No candidate, auditor, or container invocation is authorized or claimed by this file.

## H/T/D/C/U

- **H:** On a finite, frozen task/effect family, at least one hysteresis-induced final-mode divergence rejected by the existing mode-equality gate is benign for all declared hard effect, authority, release, and critical-response predicates while saving a declared decision-boundary cost; and at least one superficially benign divergence is harmful (missed deadline, unsafe prefix, authority mismatch, or wrong continuation). If either witness cannot be independently specified, retain exact mode equivalence as the simpler contract.
- **T:** Reuse the published T0 source and raw traces as immutable inputs, but do not relabel or alter its `FAIL_SAFETY_OR_REFERENCE_GATE`. Define an independent effect oracle before candidate policy evaluation. Enumerate every prefix for raw threshold, fixed hysteresis, and minimum dwell on identical exogenous traces. Include: (1) distinct modes with identical safe terminal effects; (2) missed critical/authority boundary; (3) matching final mode after an unsafe prefix; (4) stale/gap/UNKNOWN rebootstrap; (5) no-op escalation with real boundary cost and unchanged effect. Report original mode-equality columns alongside effect/safety/cost/UNKNOWN results.
- **D:** `METHOD_PASS_SCOPED` only if a separately implemented raw-only auditor reconstructs every prefix and labels both planted benign and harmful divergences correctly, with no false-safe hard predicate. Any false-safe is FAIL; missing effect oracle, critical deadline, or authority lineage is HOLD/STOP. A later hysteresis-benefit claim requires a preregistered measured boundary-cost reduction and no hard-predicate regression; equality of final labels alone is insufficient.
- **C:** Exact mode equality may be preferable if the richer oracle is costly or incomplete; scheduler/backpressure may reduce interruptions without policy-mode divergence.
- **U:** Finite synthetic effects can miss hidden/delayed GUI consequences; scalar boundary cost and deadlines may not transfer. No live, calibrated-risk, latency, token, or task-performance claim.

## Provenance and execution gate

Scientific parent: [Issue #5352](https://github.com/Unjuno/agent-interface/issues/5352), clarification [comment #5944191631](https://github.com/Unjuno/agent-interface/issues/5352#issuecomment-5944191631). Preserve prior T0–T14 and PR #5376/#5576/#6371 evidence byte-for-byte; this proposed T15 is a distinct successor, not a reinterpretation.

Before formal work: inspect source/raw availability and SHA-256 on current main; freeze an additive branch/path and unique output/allocation; verify an explicit non-overlapping WSLc CPU assignment, shared-runtime owner release and current WSLc resource/network state; predeclare exact cached image digest/platform and bounded commands. Candidate once, separate independent raw-only auditor once only after candidate exit 0; no retry. If a gate fails, preserve a STOP record and do not claim a scientific result.

Current execution disposition: **HOLD — no #5352-specific CPU/WSLc allocation is recorded.** This preregistration does not request, reserve, or grant a slot.
