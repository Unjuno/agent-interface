# Issue #6147 T0 A03 — safe distinguishing probes under observation aliasing

**Disposition: `FAIL_AUDIT_CONTROL_COVERAGE` (method PASS not established).** Candidate exited 0 and emitted a 13,433-byte raw result. The frozen auditor exited 0 and independently reconstructed all 9 finite depth layers, including policy trees, counts, canonical digests, selected optimum, leaf beliefs and reachable effect envelopes. However, a final qualification found that the auditor did not actually inject an unsafe-probe policy and assert rejection; it only checked that the selected probe belonged to its safe alphabet and that `u` was absent. The auditor's printed `PASS_METHOD_SCOPED` and “5 mutation controls” summary therefore overstate the preregistered D gate. No correction or rerun was made after the one-shot allocation. The exact first outcomes remain preserved; the Issue hypothesis is not declared passed or failed by these incomplete controls.

## Result

| Fixture | Trees by depth 0/1/2 | Resolved trees by depth 0/1/2 | Selected result |
|---|---:|---:|---|
| Action-different, safely separable | 1 / 4 / 13 | 0 / 0 / 1 | `p` then output-conditioned `q`; minimum depth 2, terminal outputs `LEFT`/`RIGHT` |
| Action-equivalent alias | 1 / 1 / 1 | 1 / 1 / 1 | Immediate `ACTION_EQUIVALENT`, not hidden-state identity |
| Action-different, safe-bisimilar | 1 / 4 / 13 | 0 / 0 / 0 | `YIELD`; no safe policy through depth 2; exact closed relation preserves safe-output ambiguity |

The unsafe informative probe `u` is outside the frozen admissible alphabet and is absent from the enumerated candidate policies. The auditor independently reconstructs all admissible trees, checks all fixed safe words through depth 2 (complete for these deterministic two-hypothesis fixtures), verifies the stated bisimulation relation is output-equal and transition-closed for every safe probe, and explicitly rejects the dropped-branch, aliased-singleton, non-closed-relation and same-image-recapture cases. It did **not** exercise the unsafe-probe injection as a rejection control. See [`QUALIFICATION.md`](QUALIFICATION.md). The raw records every output-conditioned branch and every leaf's action/effect envelope.

## Execution and evidence

- Allocation: `AI-6147-T0-20261003-03`; distinct prospective successor. A02 remains untouched: its single candidate exited 1 after writing raw and was `STOP_CANDIDATE_RUNTIME_ERROR / NOT_EVALUATED`; it is neither reused nor reinterpreted.
- Base: main `b521912b9da1fa292f2e4fed1f1ae695c4a7658e`.
- Frozen host: CPython 3.14.5, standard library only. Formal commands, one invocation each: `python3 -I candidate.py` (exit 0), then `python3 -I auditor.py RAW.json` (exit 0). Candidate and auditor used no shared code/import; the auditor consumed raw only.
- Candidate raw: 13,433 bytes; SHA-256 `97e7628f60999f36945829abe52357570e83716da5e8b92051baec4e02df3e82`.
- Source hashes and exact preregistered gate: [`FREEZE.md`](FREEZE.md). Plan: [`PLAN.md`](PLAN.md). Raw: [`RAW.json`](RAW.json).
- Runtime scope: host CPU only; no model, GPU, GUI, network, physical input, Docker, or OrbStack. No shared container resource was touched. This is consistent with #6147's explicitly analytical/no-model T0; it is not container evidence.
- Construction checks (syntax compilation and in-memory generation) passed before freeze and are not counted as formal outcomes. Formal candidate and auditor each ran exactly once; no retries or tuning.
- Local repository index CI passed. The frozen auditor's claimed PASS is qualified as `FAIL_AUDIT_CONTROL_COVERAGE`; see the preserved first outcomes and exact gate miss above.

## C / U

A typed application query or ordinary YIELD may be simpler and safer; the apparent separation may be an artifact of the authored transition table. The action-equivalence label is an explicit fixture annotation, not independently established real-app evidence.

This result covers only the stated finite deterministic synthetic machine. It does not establish real GUI finiteness/stationarity, hidden-state completeness, safety or non-destructiveness of any real probe, reset validity, effect truth, task correctness, authority, product safety, latency, or transfer to user workflows. No runtime component or policy is promoted.
