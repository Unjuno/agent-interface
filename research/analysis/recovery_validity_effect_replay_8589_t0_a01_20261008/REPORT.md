# Issue #8589 T0 A01 result

**Disposition: `PASS_METHOD_SCOPED`.** The frozen candidate and independent audit each ran once in WSLc; both exited 0. The auditor reconstructed all 8/8 cases with zero errors, rejected all 5/5 frozen mutations, and observed zero effect dispatch attempts. Retries: 0.

## Result

The finite corpus exhausted all four revision schedules for two independent branches (neither changed, left only, right only, both). It also contained a paired left-revision/incomplete-provenance case, ambiguous effect delivery, a verified no-effect receipt, and a Boolean-versus-integer version alias.

Across all eight cases, declared computational recomputations were 40 for FULL_RESTART, 14 for EARLIEST_CONFLICT_SUFFIX, and 12 for SELECTIVE_VALIDITY_RECOVERY. This is a count on the authored fixture, not a time/cost measurement. Selective recovery used strictly fewer recomputations than suffix recovery in two cases: `revision_left` and `boolean_version_alias`. The left-only complete case preserved four independently valid nodes while recomputing only `derive_left`; suffix recovery also recomputed `derive_right` and `prepare_right`. Its paired incomplete-provenance case returned `HOLD_INCOMPLETE_PROVENANCE` with zero selectively reused nodes. Ambiguous delivery returned `HOLD_EFFECT_RECONCILIATION`; the output contained no dispatch. The verified-no-effect receipt also did not authorize dispatch. The type-alias case treated Python Boolean `true` as invalid for the integer generation contract and recomputed the affected branch.

All frozen audit gates passed:

- eight candidate cases matched the auditor's independent reconstruction;
- five controls rejected: missing dependency edge, stale generation reused, forged no-effect receipt, dispatch despite an idempotency assertion, and replay after ambiguous delivery;
- strict selective advantage occurred in two authored cases;
- incomplete provenance reduced selective reuse from four to zero and forced HOLD;
- dispatch attempts: zero.

The exact raw records are `results/candidate_raw.json` and `results/audit.json`. The audit digest and raw-output digest are in `SHA256SUMS`.

## Formal environment and exact commands

WSLc 3.0.1.0, Python 3.12.14, Linux amd64, image `python:3.12-slim`, immutable image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, image digest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. Network disabled. No dependencies installed; no model, GUI, user data, GPU, credentials, or external effect. The candidate container did not mount `truth.json`; the auditor received the candidate's raw file after its one-shot exit.

Candidate invocation (one time, exit 0):

```powershell
wslc.exe run --rm --network none -v 'C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\_research_8589_selective_recovery_a01_20261008\research\analysis\recovery_validity_effect_replay_8589_t0_a01_20261008\candidate.py:/src/candidate.py' -v 'C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\_research_8589_selective_recovery_a01_20261008\research\analysis\recovery_validity_effect_replay_8589_t0_a01_20261008\run_candidate.py:/src/run_candidate.py' -v 'C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\_research_8589_selective_recovery_a01_20261008\research\analysis\recovery_validity_effect_replay_8589_t0_a01_20261008\input.json:/in/input.json' -v 'C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\_research_8589_selective_recovery_a01_20261008\research\analysis\recovery_validity_effect_replay_8589_t0_a01_20261008\results:/out' -w /src python:3.12-slim python /src/run_candidate.py /in/input.json /out/candidate_raw.json
```

Auditor invocation (one time, exit 0):

```powershell
wslc.exe run --rm --network none -v 'C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\_research_8589_selective_recovery_a01_20261008\research\analysis\recovery_validity_effect_replay_8589_t0_a01_20261008\auditor.py:/audit/auditor.py' -v 'C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\_research_8589_selective_recovery_a01_20261008\research\analysis\recovery_validity_effect_replay_8589_t0_a01_20261008\run_audit.py:/audit/run_audit.py' -v 'C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\_research_8589_selective_recovery_a01_20261008\research\analysis\recovery_validity_effect_replay_8589_t0_a01_20261008\input.json:/audit/input.json' -v 'C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\_research_8589_selective_recovery_a01_20261008\research\analysis\recovery_validity_effect_replay_8589_t0_a01_20261008\truth.json:/audit/truth.json' -v 'C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\_research_8589_selective_recovery_a01_20261008\research\analysis\recovery_validity_effect_replay_8589_t0_a01_20261008\results:/out' -w /audit python:3.12-slim python /audit/run_audit.py /audit/input.json /audit/truth.json /out/candidate_raw.json /out/audit.json
```

## Construction and repository verification

- WSLc standard-library suite: 11/11 passed.
- WSLc `python -O` suite: 11/11 passed.
- Repository analytical index unit tests: 22/22 passed.
- `research/check_workspace_index.py`: passed, 163 top-level research directories reachable. The `outputs/` navigation entry was added identically to the concurrent #8588 index fix.
- `git diff --check`: passed before formal execution.
- The local analytical generated-index checker was not treated as complete evidence because this worktree uses sparse checkout. The full-repository Analysis Index GitHub check is still required before integration.

Expected construction RED runs (missing not-yet-written candidate/auditor/runner modules) and a corrected inconsistent test fixture are documented in `CONSTRUCTION_LOG.md`. They are not formal failures and no formal outcome was rerun or replaced.

## Interpretation and limits

This supports only a finite-method claim: for this authored DAG and these cases, separating reusable computation from external-effect dispatch admits a plan that retains some valid independent work without automatic effect replay. It is not evidence of real workflow savings, GUI correctness, safe live retry, compensation safety, latency/token reduction, or broad recovery behavior. A verified effect is historical evidence, not authority for a new action; even a verified no-effect receipt does not dispatch anything in this planner. Any runtime implementation, live application test, or user study requires a separately scoped and authorized successor.

The external sources establish structured workflow/MVCC recovery in their own domains, not this GUI-like result: [REVISE](https://arxiv.org/abs/2609.00643), [MVCC conflict repair](https://arxiv.org/abs/1603.00542). Their reported system-level benefits are not transferred here.
