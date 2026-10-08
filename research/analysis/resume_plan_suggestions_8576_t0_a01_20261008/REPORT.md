# Issue #8576 T0 A01 — formal result

**Disposition: `PASS_METHOD_SCOPED`.** Frozen candidate and independent auditor each ran once in WSLc, both exit 0. The auditor reconstructed all 12 cases with zero errors and rejected all six preregistered output mutations. Retries: zero.

## Findings

The candidate emitted four suggestion rows representing three distinct public-state patterns: the unique initial checkpoint (`open`), the unique checkpoint after a public completion receipt (`configure`), and the identical paired public state (`capture`). The paired rows had identical contract/state/provenance and decision despite different sealed hidden labels. The eight other rows abstained: ambiguous alternatives, stale state, wrong window, changed task, completed contract, cancelled predecessor, unresolved effect, and no contract. Every row carried `authority: none` and `freshness: snapshot_requires_revalidation`.

This is a method result about a small authored contract schema. It does not show that an actual person accepts, edits, or benefits from suggestions.

## Execution record

- Freeze commit: `091e33a15fd8c27d73fb4acd0496df79457f8e77`; frozen base main: `28b6f0fc0dd3cf6d798d97ee608a409ce773e409`.
- Runtime: Microsoft WSLc 3.0.1.0; cached `python:3.12-slim`, image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`; Python 3.12.14; linux/amd64; `--network none`; no Docker Desktop.
- Candidate and auditor ran sequentially in one fresh `--rm` container from the frozen checkout. Candidate exit 0 wrote `results/candidate_raw.json` (4,858 bytes); only then auditor exit 0 wrote `results/audit.json` (959 bytes).
- Audit: `PASS_METHOD_SCOPED`, 12/12 cases, zero reconstruction errors, six mutations rejected.
- Construction: 3 tests passed normally and under `python -O`, each in WSLc with a read-only bind. A preformal malformed-graph RED test caught a duplicate-checkpoint validation defect; after the candidate fix, focused and full construction tests passed. No formal output was produced during construction.
- Baseline repository analysis-index tests passed 22/22. The separate workspace index initially exposed the pre-existing `outputs/` namespace omission on the frozen main base; PR #8588 carries that additive repair. This did not affect the experiment or its audit.

## Scope and limitations

No users, participants, model, GUI, application, network, or continuation action were involved. No preparation-time, accuracy, anchoring, usability, cognitive, accessibility, safety, reliability, or product-benefit claim follows. A T0 method PASS is not approval for a human study; a later human-benefit study requires separate ethics/privacy/accessibility review, consent, and preregistration. WSLc was used for local deterministic CPU iteration; no CPU/memory enforcement or general Docker-replacement claim is made.
