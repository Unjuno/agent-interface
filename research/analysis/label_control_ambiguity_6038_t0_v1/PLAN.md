# Issue #6038 T0 — label/control binding ambiguity (method only)

## H / T / D / C / U

**H.** On frozen synthetic form layouts, a relation-aware bind-or-abstain rule can preserve the requested field→control relation when nearest geometry and coarse perceptual grouping select a different control, and can abstain when permitted evidence does not uniquely identify a control. A finite fixture is not evidence of real GUI prevalence or safety.

**T.** Allocation `LABEL-CONTROL-AMBIGUITY-6038-T0-20261002-01`. Ten deterministic cases encode the exact visible frame, label/tooltip text and role, scope, control geometry, optional current-generation trusted relation, and declared visual candidate edges. A separate oracle file contains the expected effect target and initial field values; it is never mounted into the candidate container. Policies: (1) exact-text nearest geometry, (2) same-scope perceptual grouping, (3) current trusted relation, otherwise unique declared visual edge, otherwise abstain. All policies first fail closed on frame/tree generation mismatch. Candidate runs once; independent auditor runs once after candidate exit 0. No retries.

Cases: unambiguous positive; two-column proximity conflict; staggered distant aligned label; repeated label text in separate scopes; near tooltip decoy; fresh trusted relation contradicting proximity; unresolved two-control ambiguity; stale frame/tree; stale trusted relation with non-unique visual candidates; unique visual-edge positive without a programmatic relation. Scoring is final field state, not widget detection, click delivery, or Save dispatch.

**D.** `PASS_METHOD_SCOPED` only if the independent auditor reconstructs every policy decision and final field state, relation-aware resolves all eligible unique cases to the exact oracle field, abstains on all ambiguous/stale cases, both positive controls still complete, and all frozen mutations are rejected. Any wrong field write is a hard method failure; missing or contradictory oracle evidence is HOLD. Method PASS is not a live GUI/model/task claim.

**C.** Synthetic geometries may exaggerate ambiguity; a trusted accessibility relationship can be wrong; coarse grouping or current GUI semantics may dominate pixels; abstention has cost.

**U.** No real screenshot, GUI, accessibility tree, model, user data, application action, privacy/security rate, or production safety evidence. The candidate sees only declared observations; the independent semantic/effect oracle is audit-only.

## Frozen protocol

- Base: `d7e20a0d25e0c361d1e7cf56fd103f61fb927a2d` (origin/main at source freeze).
- Image: `python:3.12-alpine`, pinned local image ID and platform recorded in `FREEZE.json`/`RUN.md`; no pull.
- Separate network-disabled candidate and auditor containers; source/fixture/oracle read-only; resource-limited CPU/memory/PIDs; read-only root; no capabilities; no-new-privileges.
- Formal invocation count: candidate 1, auditor 1, retries 0. Candidate sees no oracle; auditor sees candidate raw and both frozen inputs.
- Frozen outputs: candidate decision rows plus auditor exact reconstruction, per-policy effect score, and mutation-control results.

## Local preparation

Only construction tests and syntax/hash checks may run before formal execution. Formal raw files are created only by the two one-shot container invocations. Preserve any mismatch as-is; do not repair and rerun this allocation.
