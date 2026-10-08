# Issue #6053 T1 — PCAA stage-propagation eligibility

**Disposition: `HOLD_NO_ELIGIBLE_CHAIN`.** The current Procedural Control Arena v1 exposes a useful per-stage event/result ledger and effect-based task scoring, but it does not provide matched exogenous perturbation versus unperturbed trajectories or a re-grounding/checkpoint arm. Its single `RECOVERY` primitive is an authored within-task target relocation, not an independently assigned upstream disturbance followed through a matched stage chain. The benchmark README also explicitly says the source tree is not a hardened secrecy boundary; it does not establish held-out controller/evaluator isolation.

## H / T / D / C / U

**H:** The Issue #6053 hypothesis remains unresolved: a bounded upstream perturbation may amplify or contract through a serial computer-control chain, and checkpointed re-grounding may change that propagation. T1 asks whether the current #4695 PCAA v1 is an eligible existing chain for testing it.

**T:** Read-only AST/source audit of the current `main` PCAA v1 runner, engine, test file, evaluation criteria and README. Inputs are pinned in `FREEZE.json`. `audit.py` checks exact SHA-256 identities and reports CLI/session/event/report structure, any matched perturbation/counterfactual path, and the stated isolation boundary. No arena episode, GUI, input, model, container, or formal pair was run.

**D:** `HOLD_NO_ELIGIBLE_CHAIN` if the current arena lacks a matched exogenous perturbation path or cannot establish source/process/seed isolation for held-out execution. `RESULT.json` records this outcome. The audit found:

- Stage-indexed events and `stage_results` exist. This supports descriptive stage attribution, but not a matched perturbation trajectory.
- `RECOVERY` has an authored `recovery_displacement` difficulty axis and causes a scripted target relocation after the first correct click. That is a perturbation within the recovery task, not an upstream disturbance independently assigned to a preceding stage. There is no CLI or engine arm that compares the same frozen chain with and without that disturbance, or with versus without checkpointed re-grounding.
- `BenchmarkSession` produces effect-based success/failure, stage results and an event ledger in the same engine process. This is a useful benchmark oracle for its primitives, but no separately replayed oracle or source-isolated formal pair is established here.
- `public_state()` omits the seed and hidden IDs. However, `arena.py` and the `BenchmarkSession` object run in one process, and the README explicitly says the source tree is not a hardened secrecy boundary. The seed is included in the final report. This does not establish that an evaluated controller cannot inspect process/source state during a formal run.

**C:** #4695's recovery task could be interpreted as one fault exposure. That is insufficient for #6053's declared T1 because it is not a matched exogenous disturbance control and does not compare the same chain under no disturbance and re-grounding. Per-stage correct actions can still be studied in a future eligible setup, but the arena's existing results cannot answer the proposed propagation contrast.

**U:** This source audit does not establish whether perturbations actually amplify in any Agent Interface chain, whether re-grounding helps, or whether the existing Arena could be adapted with a separate harness. A repository-wide content scan was not completed: the partial-clone `git grep` did not return within the bounded command window, and GitHub code search returned 404. The scope is the pinned PCAA source and #4695's retained benchmark status, not a proof that no separately named external harness exists. The HOLD is about current Arena-source eligibility only. No claim about GUI performance, safety, or controller capability follows.

## Reproduction and provenance

From the repository root, run:

```text
python3 research/analysis/pcaa_stage_propagation_6053_t1_20261004/audit.py
```

The audit reads only the exact five source files pinned in `FREEZE.json`, emits deterministic `RESULT.json`, and exits nonzero on a source-hash mismatch. The exact base is `9590ee9e0c74f7438306e8efb48b2af813f7a86b`. No candidate or formal allocation was consumed, and no existing #4695 or #6053 evidence was modified.
