# Issue #5793 T0 — consent-scoped preparation in a finite UI simulator

**Disposition: `PASS_METHOD_SCOPED`.** The frozen finite fixture demonstrates one repeated-task regime where a session-scoped preparation amortizes the declared observation cost while preserving exact effects, warning visibility and restoration, and a heterogeneous regime where that preparation is refused before consequential input because it hides a critical warning. This is not live GUI, actual human-consent, natural workload, model-token, wall-time, or general efficiency evidence.

## H / T / D / C / U

- **H:** In a finite fixture, one explicitly consent-scoped session preparation can reduce total declared cost versus both no preparation and repeated per-task preparation for repeated targets, but cannot be treated as valid on a heterogeneous family when a critical warning becomes occluded.
- **T:** Compared A=no preparation, B=prepare/restore each task, C=prepare once/restore once. Positive task order A1/A2/A3 repeats panel A. Negative order A1/B1 makes panel-A preparation hide a critical warning in B. Controls cover partial restoration, competing generation edit, and irreversible callback collateral. Candidate ran once and an independent raw-only auditor ran once; formal retries=0.
- **D:** `PASS_METHOD_SCOPED`: positive session arm was cheaper than both completed controls with exact effects, visible warnings, unchanged user state and verified restoration; heterogeneous session arm deferred before consequential action and did not claim a completed total cost; all three fail-closed controls matched; independent audit had no errors and all four corruption controls were rejected.
- **C:** Internal evidence compression/adaptive per-task views may provide similar benefits without persistence. Fresh instances may be cheaper and simpler. A finite simulator can exaggerate amortization and omits actual app callbacks.
- **U:** All costs are synthetic units, not measured tokens, latency or human effort. Receipt consent is a fixture label, not actual consent. No desktop/app/model/GPU/shared runtime/user setting was touched. No natural task distribution, accessibility preference, or cross-app transfer is established.

## Formal result

| Family / arm | disposition | total or incurred synthetic cost | observations | correctness/safety |
|---|---:|---:|---:|---|
| Repeated A=no prep | COMPLETE | 15 | 6 | exact effects; warnings visible; restore verified |
| Repeated B=per-task | COMPLETE | 18 | 3 | exact effects; warnings visible; restore verified |
| Repeated C=session | COMPLETE | 12 | 3 | exact effects; warnings visible; user state unchanged; restore verified |
| Heterogeneous A=no prep | COMPLETE | 10 | 4 | exact effects; critical warning visible |
| Heterogeneous B=per-task | COMPLETE | 12 | 2 | exact effects; critical warning visible |
| Heterogeneous C=session | DEFERRED_SAFETY | incurred 8 only | 3 | warning hidden; consequential actions after detection 0; no completed total assigned |

Declared unit weights: task work=1/task, observation=2/observation, preparation=2/preparation, restoration=1/restore. These are stipulated simulator values, not measurements. The heterogeneous session arm is safety-ineligible; its partial incurred cost is not ranked against completed arms.

Controls: partial restore=`UNKNOWN_RESTORE`; competing app-generation change=`DEFERRED_STALE_GENERATION` with consequential actions 0; callback journal/user-state collateral=`REJECTED_COLLATERAL`, restoration false. Each session receipt binds task-owner scope, disposable-session consent label, app generation, expiry and independent snapshot restoration plan.

## Provenance and audit

- Allocation: `consent-scoped-preparation-5793-t0-docker-20261001-01`.
- Source freeze base: `8ba30d5bf79358afdd5e6c7359d4b132be6f33ed`; main advanced independently during the run. The probe reads/writes only its isolated mounted fixture/output and does not depend on later main changes.
- Environment: Docker Desktop 29.8.0, Linux/amd64, Python 3.12.14; image `agent-interface-readiness-a3:local-20260927`, ID `sha256:a89e10813abd763a71b88055d51737d5e827fe3b5e473a583156b65eef20105f`; network none, 1 CPU, 256 MiB, 64 pids, read-only source/root with separate output mount.
- Construction: 5 unittest checks passed before freeze. One red construction test found that a safety-deferred arm carried a misleading `total_cost`; it was corrected to `incurred_cost` only, then all five checks passed.
- Formal: candidate invocation 1; independent auditor invocation 1; retries 0. Raw and audit hashes are in `SHA256SUMS`.
- Auditor imports no candidate code; it independently checks schedules, exact costs, consent receipt scope, warning/effect gates, restoration, stale-generation refusal, collateral, and four mutation controls.

## Reproduction

From this directory in the pinned local container:

```powershell
python -m unittest -v test_probe  # pre-freeze construction only
python candidate.py --formal      # formal invocation; once only
python audit.py                   # independent audit; once only
```

Formal source/environment identities are frozen in `FREEZE.json`. `construction/` contains pre-freeze outputs separately from the immutable formal files in `out/`.

## Integration and scope boundary

Evidence is additive under `research/analysis/consent_scoped_preparation_5793_t0_v1/`. This is a method-only finite-model result, not permission or authorization for persistent changes on a personal desktop. Any live successor needs a disposable isolated GUI, actual task-owner consent, independent full-state/callback oracle and explicit restoration evidence.
