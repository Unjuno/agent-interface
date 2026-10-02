# Issue #6515 — planner-blind credential-entry T0

## Outcome

Allocation 03 returned `PASS_METHOD_SCOPED`: the raw-only auditor reconstructed all 75 expected rows with zero errors and rejected all 8/8 corruption controls. This is a finite policy-model consistency result, not a test of an executable credential provider, not evidence of real secret confidentiality, and not authorization for T1.

## Hypothesis / method

The tested issue idea is that a request-bound secret-entry policy should refuse wrong-origin, stale-generation, expired/replayed-handle, scope-mismatch, and unsupported-route contexts, while preserving UNKNOWN when origin/effect evidence is absent. The fixed fixture has 15 synthetic contexts crossed with five profiles: actor-only typing, visual-only typing, a documentation-only transcription of the agent-browser provider contract, a synthetic request-bound broker, and manual/no automation. No credential bytes, real handle, account, browser, network, GUI, human, clipboard or OS input was used.

The documented provider profile is not the product or plugin executable. Where published documentation does not establish expiry, replay, embedded-origin or effect semantics, the model retains UNKNOWN. Boolean leakage indicators are assertions in the policy model; no dynamic information-flow trace was performed.

## Allocation history

- Allocation 01 (`c33380b3b08792a331ee11f7aee05e3d41437e3e`): `STOP_BASE_ADVANCED_BEFORE_RUN`; zero candidate/auditor invocations.
- Allocation 02 (`2ebde9d05592a3a8f866fafcb4cbef888f53d199`): `STOP_BASE_ADVANCED_BEFORE_RUN`; zero candidate/auditor invocations.
- Allocation 03 (`e7f11cdc2cdee42b0f745add6c4a93fc641abe6d`): prelaunch equality/hash/output-absence gate passed; candidate and auditor each invoked once.

The first two freezes and stop records are preserved unchanged. Allocation 03 raw and audit outputs are in `results/formal_03/`.

## Verification

- Construction suite: `python3 -W error::ResourceWarning -B -m unittest -v test_t0` — PASS 7/7.
- Formal run: 75 rows, zero audit errors, 8/8 corruption controls rejected — PASS_METHOD_SCOPED.
- Local `Analysis Index` workflow checks: index checker and this package's construction suite passed; the workflow's remaining listed analytical suites passed except two frozen-workflow provenance assertions. Those two expect `.github/workflows/analysis-index.yml` to be restored to pinned commit `e2e434d...` (hash `b19000e...`) by the workflow's preceding CI-only step; the local checkout instead has the current workflow (`9e5679...`). They are environment/precondition failures in the manually invoked sequence, not failures in this package. The authoritative Actions run must still confirm the full workflow.
- Scope: no product/security verdict, real credential/provider behavior, actual authentication effect, byte-flow guarantee, GUI/user evidence, or product-benefit evidence.
- Runtime: host CPython stdlib; container intentionally not used because the shared OrbStack/Docker allocation was unassigned and WSLc was prohibited by the current #5085 gate.

## Decision

Retain as a bounded T0 method result. Do not claim that a real provider is planner-blind or secure from this synthetic comparison. Any successor should exercise an isolated, explicitly assigned provider/runtime with synthetic credentials and an independent effect oracle, after the runtime ownership gate allows it.
