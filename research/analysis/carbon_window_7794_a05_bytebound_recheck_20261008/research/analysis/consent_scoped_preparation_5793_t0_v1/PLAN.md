# Issue #5793 T0 — consent-scoped reversible preparation

## Intent and scope

This is a bounded research spike for the explicit #5793 question: test whether a task-owned, reversible view preparation can amortize observation cost over repeated tasks while losing or refusing under heterogeneous tasks and externalities. The user's persistent project direction is experiment-first, container-first when feasible, additive publication, and explicit scope limits. No persistent desktop preference, personal UI, production runtime, live GUI, model, network, or GPU is touched.

## H / T / D / C / U

- **H:** In a finite fixture, one explicitly consent-scoped session preparation can reduce total declared cost versus both no preparation and repeated per-task preparation for a repeated-target task family, but it must not be treated as a valid completion on a heterogeneous family when a critical warning becomes occluded.
- **T:** Model three arms: A no preparation, B prepare/restore per task, C one session preparation and final restore. Positive family: A1/A2/A3 share panel A. Negative family: task A then task B has a critical warning obscured by the panel-A preparation. Include partial restoration, a competing generation edit, and irreversible callback-collateral controls. A separately implemented auditor reconstructs costs and safety outcomes from raw JSON. Construction tests precede freeze; after freeze run candidate once and auditor once, no retries.
- **D:** `PASS_METHOD_SCOPED` only if C is cheaper than A and B for the completed repeated family, exact effects and warning visibility are preserved there, the heterogeneous C arm refuses before consequential input and is not assigned a completed total cost, and partial restore/collateral/stale-generation controls fail closed. Any misreported completion or unsafe input is `FAIL_METHOD`; unreconstructable evidence is `STOP/HOLD`. This proves only the encoded finite model.
- **C:** Internal evidence compression/adaptive per-task views may deliver similar savings without persistence. Fresh instances may be simpler than preparation. A finite simulator may exaggerate savings or omit real application callbacks.
- **U:** Cost units are declared synthetic weights, not model tokens, wall-clock or user effort. No live human consent, accessibility preference, natural task distribution, GUI callback, app-generation or cross-app transfer is established. Consent receipt in the model is not real user authorization.

## Frozen synthetic cost model

Cost = task work (1/unit per task) + observation (2/unit each) + preparation (2/unit each) + restoration (1/unit each). A no-preparation task needs two observations; an eligible prepared task needs one. Repeated family has 3 tasks: A cost 15, B cost 18, C cost 12. Heterogeneous family has 2 tasks: A cost 10, B cost 12; C hides a critical warning, must stop with zero consequential actions, and reports only `incurred_cost=8` (not a completed total). Costs are deterministic fixture labels, not measurements of a real agent.

## Safety and provenance gates

Every preparation receipt binds task-owner scope, disposable-session consent label, app generation, expiry and independent restoration snapshot. The independent oracle must detect callback collateral even if the primary visible value appears restored. A competing generation change invalidates the preparation; no stale consequential action. Partial restoration is `UNKNOWN_RESTORE`, never complete. Candidate and auditor do not share verdict code.

## Environment

- Allocation: `consent-scoped-preparation-5793-t0-docker-20261001-01`
- Base main: `8ba30d5bf79358afdd5e6c7359d4b132be6f33ed` (refreshed before source freeze; empty branch fast-forwarded from its original uncommitted base)
- Image: `agent-interface-readiness-a3:local-20260927` (observed image ID `sha256:a89e10813abd763a71b88055d51737d5e827fe3b5e473a583156b65eef20105f`)
- Docker Desktop 29.8.0, Linux/amd64, Python 3.12.14; network none, 1 CPU, 256 MiB, 64 pids.
- Candidate formal invocation exactly 1; independent auditor exactly 1; formal reruns 0.

## Integration boundary

Only add `research/analysis/consent_scoped_preparation_5793_t0_v1/`. Keep the construction test/output separate from formal raw. Do not alter global README, CURRENT_GOAL, ROADMAP, runtime, prior evidence or user settings. A finite PASS is a method-only result; any live GUI successor requires a separately frozen disposable GUI, independent before/after state oracle, and explicit consent authority.
