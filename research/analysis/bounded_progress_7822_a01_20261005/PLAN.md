# Issue #7822 — bounded, evidence-grounded progress T0 A01

## Freeze

- Allocation: `BP-7822-HOST-A01-20261005`
- Base: main `4a8049327eb44b54cfcf55167adb102a710a7051`
- Branch: `research/7822-bounded-progress-t0-a01-20261005`
- Package: `research/analysis/bounded_progress_7822_a01_20261005/`
- Model: four small labelled transition systems and five policy/case checks; only transition counts, no wall-clock claim. Marker status is supplied to the auditor only, never to the controller trace.
- Safety: edges marked unsafe are excluded from all policies.
- Fairness: none. Every enabled uncontrollable edge is adversarially selectable indefinitely.
- Evidence: a task marker is true only in the separate frozen oracle; event dispatch, waiting, repetition, and sequence advancement do not establish it.

## H / T / D / C / U

**H:** Safety plus finite-trace nonblocking can leave a safe WAIT cycle forever even while a marker path remains available. A bounded-progress restriction can reach an independently evidenced marker in the positive cases; it must refuse a universal bound under an uncontrollable cycle or absent marker evidence.

**T:** Compare maximal safe nonblocking against a bounded-progress policy on: (1) safe WAIT self-cycle with a controllable marker path; (2) a forced two-event asynchronous wait followed by a marker action; (3) an uncontrollable self-cycle plus a controllable marker action; (4) a safe attempted action with no independent marker evidence. Include an unsafe forbidden edge in the positive graph. Candidate witness traces and an independently encoded graph checker are in `t0.py`. The checker computes reachable states, marker coreachability, non-marker cycles, worst-case transition distance and safety independently; it also checks five raw-output corruption controls.

**D:** PASS_METHOD_SCOPED requires: the ordinary supervisor is SAFE_NONBLOCKING but admits a non-marker cycle; bounded positive bound is exactly 1; bounded asynchronous case is exactly 3 transitions; the adversarial uncontrollable cycle yields PROGRESS_NOT_GUARANTEEABLE despite finite marker reachability; missing marker evidence yields SAFE_YIELD; no unsafe edge is enabled; all checker mutations are rejected. Any mismatch is FAIL. A missing or leaked oracle marker is HOLD/FAIL, never completion.

**C:** A simpler YIELD/no-progress handler may suffice in deployed systems. The synthetic controller may encode the answer in its policy, and no practical liveness benefit follows from this fixture.

**U:** Finite authored graphs; no partial observation, human/model delays, real task markers, GUI, runtime, or effect. Transition bounds are not time bounds. No fairness is assumed. No live allocation or safety guarantee is implied.

## Execution environment

C: had 0 bytes free at freeze, so no local/container writes were possible; WSLc was not used. The exact committed script will be run in memory using host CPython 3.11.9. This is an explicit environment deviation, not a container-equivalent result. Candidate evidence and checker output will be retained additively after the single invocation. No network, model, GUI, game, external effect, or user data.
