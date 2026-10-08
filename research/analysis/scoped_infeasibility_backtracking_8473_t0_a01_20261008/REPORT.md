# Issue #8473 T0 A01 — scoped infeasibility feedback

**Disposition: `PASS_AUDIT_V2` / method-scoped for the finite authored fixture only.** The A04 audit-only challenge rechecked the immutable A03 candidate output against the independent exhaustive oracle and concretely corrupted fixture/raw controls. A03's original mutation checks were later judged too structural; its original outputs remain preserved, and A04 supplies the strengthened audit gate. This is not evidence about a real GUI, screenshot-grounded feasibility, a planner model, runtime safety, latency, or task success.

## H / T / D / C / U

- **H:** In a finite symbolic planner, a verified low-level blocker retained only for the same action, target, surface, and evidence generation will reduce repeated equivalent infeasibility queries without pruning an available recovery plan.
- **T:** Exhaustively evaluate NO_FEEDBACK, GLOBAL_BLACKLIST, and SCOPED_NOGOOD over an occluded target with rearrangement, unavailable focus with recovery, no-alternative infeasibility, and a stale observation followed by a generation change. Independently enumerate feasible plans and apply five mutations.
- **D:** PASS_AUDIT_V2 only if independent labels agree, scoped feedback reduces duplicate queries, retains recovery alternatives, invalidates on generation change, never treats timeout as impossibility, and five concretely mutated inputs are rejected. A01/A02 STOP and A03 initial audit remain immutable.
- **C:** Stateless replanning can already recover when alternatives are explicitly proposed; scoped memory adds invalidation complexity. The global blacklist comparator can appear to save queries by incorrectly deleting recovery plans.
- **U:** The model has perfect symbolic state and a supplied feasibility truth table. It omits screenshots, partial observation, concurrent change, realistic planner proposals, action execution, tokens, time, and GUI semantics.

## Formal execution

- Allocation: `8473-SCOPED-INFEASIBILITY-T0-A03-20261008-01` (audit-assertion repair after preserved A01 formal STOP and A02 formal STOP; candidate/fixture unchanged; final auditor SHA-256 `d7effb078a3be9f9307e1058b59fd0699ab1b4499a29cd6df113d1ee3b358dd7`).
- Base: `origin/main` commit `eeec9a355adc82ccd4cace8ea36f145a60c8805f`.
- Candidate command, invoked once: `python3 -B research/analysis/scoped_infeasibility_backtracking_8473_t0_a01_20261008/candidate.py research/analysis/scoped_infeasibility_backtracking_8473_t0_a01_20261008/fixture.json research/analysis/scoped_infeasibility_backtracking_8473_t0_a01_20261008/results/a03/candidate.raw.json` (exit 0).
- Auditor command, invoked once: `python3 -B research/analysis/scoped_infeasibility_backtracking_8473_t0_a01_20261008/audit.py research/analysis/scoped_infeasibility_backtracking_8473_t0_a01_20261008/fixture.json research/analysis/scoped_infeasibility_backtracking_8473_t0_a01_20261008/results/a03/candidate.raw.json research/analysis/scoped_infeasibility_backtracking_8473_t0_a01_20261008/results/a03/AUDIT.json` (exit 0; `passed=true`, 4 cases, 12 policy rows, 0 errors).
- For the repeated occluded proposal, NO_FEEDBACK made 2 equivalent infeasibility queries; SCOPED_NOGOOD made 1 and selected the valid rearrangement plan. GLOBAL_BLACKLIST made 1 but selected no plan, so its apparent query saving is an invalid result. Focus recovery and transient-after-refresh alternatives were retained; the truly-infeasible case selected no plan.
- Independent oracle feasible plans: `rearrange-then-open`, `refocus-then-type`, and `same-action-after-refresh`; none for `truly-infeasible`.
- All five controls detected: omitted/mismatched blocker, global overgeneralization, stale generation-key reuse, timeout promoted to impossibility, and deletion of a feasible alternative.
- A04 formal audit-only command, invoked once: `python3 -B research/analysis/scoped_infeasibility_backtracking_8473_t0_a01_20261008/audit.py research/analysis/scoped_infeasibility_backtracking_8473_t0_a01_20261008/fixture.json research/analysis/scoped_infeasibility_backtracking_8473_t0_a01_20261008/results/a03/candidate.raw.json research/analysis/scoped_infeasibility_backtracking_8473_t0_a01_20261008/results/a04/AUDIT_V2.json` (exit 0; baseline passed, each of five concrete mutations was rejected for its expected condition).
- Host: macOS arm64, CPython 3.14.5, standard library only. No network, model, GUI, OS input, GPU, or runtime change.
- Container inspection failed with OrbStack content-store `operation not supported` on image listing/inspect. No pull, repair, or retry was attempted. Host-only path is justified by this deterministic standard-library finite test and established repository precedent; container behavior is not claimed.

## Preserved execution chain

| Allocation | Outcome | Evidence |
|---|---|---|
| A01 | `STOP_AUDITOR_MUTATION_CONTROL` | [`A01_STOP.json`](results/A01_STOP.json), raw and audit in `results/` |
| A02 | `STOP_AUDITOR_MUTATION_CONTROL` | `results/a02/` (second audit assertion error; immutable) |
| A03 | `PASS_METHOD_SCOPED` | [`AUDIT.json`](results/a03/AUDIT.json) and raw under `results/a03/` |
| A04 | `PASS_AUDIT_V2` | [`AUDIT_V2.json`](results/a04/AUDIT_V2.json), audit-only over immutable A03 raw; concretely mutates fixture/raw controls |

A02 exposed that A01's assertion repair still tested the wrong relation. A03 changed only that auditor check; candidate and fixture stayed byte-identical. Post-run review then found A03's five mutation checks partly structural rather than adversarial input rejection. A04 strengthens the independent validator and checks all five on concrete corruptions without rerunning or altering the candidate. No failed result was overwritten or relabeled.

## Provenance and reproduction

Frozen fixture SHA-256: `c0f6eb4812dda1e5dfbd86cc71d6cc33b9a9dfc1ec4b564d1a0df148125872de`. Candidate SHA-256: `625347d60bab02b5912ab2e4354519a2da2416b1939238cbaf9a84468525ce5f`. Final A04 auditor SHA-256: `610f24df096e1817b2f26f3cb22a8bc497ff8cacfea29d795a84afa94e690e80`. A03 raw SHA-256: `ad651cbae72263dec0368ef6a812d799aa23353fd9a57ced2cbdfb5b2ac6ec51`. A03 audit SHA-256: `f294ac4d4b31e1f3b2633c779b65b5d7caeb511ca2502c2739d70ae07390d1bb`. A04 audit-v2 SHA-256: `f294ac4d4b31e1f3b2633c779b65b5d7caeb511ca2502c2739d70ae07390d1bb`.

Reproduce from repository root with the two commands above. Construction outputs and all formal outputs are retained separately. The model is deliberately finite and authored; exhaustive agreement only certifies this encoded fixture and policy simulator.
