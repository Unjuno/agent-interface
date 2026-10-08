# #8004 A02 — preregistration

## H / T / D / C / U

- **H:** A finite event-identity method test is not auditable if the candidate
  reads the oracle, omits opportunities missed by every channel, or encodes
  censoring/missing telemetry as observed nondetection. A raw-only candidate
  plus a separate oracle-only auditor should reconstruct every authored
  assignment and preserve all six known opportunities.
- **T:** Freeze `observations.json` and `oracle.json` separately. Candidate receives
  only observations; it enumerates all 2 segmentation × 2 linkage alternatives
  by constructing linked components and channel capture vectors. Auditor gets
  both inputs and raw candidate output, independently reconstructs assignments,
  per-channel truth histories, false/missed links, false merges/splits, all
  denominators, and censored/missing statuses. Include a clean temporal control,
  a crossed-link alternative, an all-channel common blind spot, heterogeneous
  detection, a right-censored opportunity, and a missing-interval opportunity.
- **D:** Construction prerequisite passes only if all five raw records appear
  exactly once per segmentation, all four assignments are present, the
  candidate output contains no truth fields, the independent auditor reconstructs
  all opportunity and channel denominators, and false/missed links plus censoring
  are separately reported. Any mismatch => HOLD/FAIL_CONSTRUCTION; this rung
  cannot pass the full #8004 H/D gates or establish the joint-only H result.
- **C:** This hand-authored 3-channel fixture can verify oracle separation and
  finite accounting, but cannot calibrate admissible assignment weights,
  represent natural continuous traces, or establish useful sensitivity bounds.
- **U:** Six authored opportunities, five observed records, 2×2 alternatives,
  host-only execution if OrbStack remains unavailable. No production traces,
  rates, safety conclusions, or posterior interpretation.

## Freeze and disposition rules

The exact two JSON inputs are the preregistered finite fixture. Do not alter them
after executing the candidate. Candidate and auditor are separate processes;
the candidate command must not name or read `oracle.json`. A final
`PASS_CONSTRUCTION_ONLY` requires D above; no result here closes #8004 T0.

## Independent truth table (frozen before candidate execution)

F1 is detected by runtime/watcher; F2 by runtime/verifier; F3 by none; F4 by
watcher only; F5 is right-censored before verifier observation; F6 falls in the
watcher's missing interval. Raw record IDs map to F1/F2/F4 only in the separate
oracle. Link hypotheses are deliberately anonymous labels and have no truth
meaning in the candidate input.
