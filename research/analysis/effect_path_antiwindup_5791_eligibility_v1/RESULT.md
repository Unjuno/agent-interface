# Issue #5791 source-bound eligibility spike v1

## H/T/D/C/U

- **H:** the current MAP01 V25 controller has no explicit accumulated correction debt that grows while an effect is blocked and remains pending until unblocked. It has one-decision no-visible-effect feedback, existing cover-policy carry-forward, and a persistent model session identifier; these are different state categories.
- **T:** parse and inspect the frozen controller source as Python AST and source-level data flow. Candidate and independent auditor each run once in a network-disabled Docker container with one CPU, 256 MiB RAM, 64 PIDs, read-only source mount, and the locally cached pinned `python:3.12-slim` image. Positive control includes `debt += delta`; negative control includes a one-turn receipt projection.
- **D:** eligible only if a correction-bearing control variable is explicitly mutated across the effect-blocked wait and carried pending to a later unblock. If absent, classify this controller path ineligible; do not infer absence of hidden model context.
- **C:** path-local static source audit only. It cannot establish behavior inside the persistent runner/provider or other controller versions.
- **U:** no execution of game, UI, model, runner, GPU, input actions, or network. This says nothing about model efficacy, real-time gameplay, or live allocations.

## Frozen inputs and environment

- Repository `Unjuno/agent-interface`, source ref initially `49db21e330768800e8b3486203b70306f4e402f6`; main advanced during preparation to `48dc8f640520f6e13ac7bd8f101cde8ee1430c9f`.
- The audited `research/doom/map01_overlap_controller_v25.py` blob was identical at both refs: Git blob SHA-1 `5a3c10cf7f5937e5f31bc27b3d7ce7ee1a357754`, 25,257 UTF-8 bytes. The local fixture copy in `controller.py` has SHA-256 `300ae84187c9fae70de9895e4a83197c64552601ff751ae5d05ed0f10809c322`, 24,939 bytes; the length difference is newline normalization during API/local transport, and the content hash binds the executed fixture.
- Docker image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Local Docker Desktop was already available; no daemon start or download was needed. Container list was empty before runs. Ollama was not needed and was stopped before execution (~95 MiB combined observed); it was not used for inference. No GPU was used.

## Result

**INELIGIBLE_FOR_THIS_CONTROLLER_PATH** for a runtime anti-windup experiment targeting accumulated in-controller correction debt.

The controller computes `effect_memory` once from only the immediately previous decision's `effect_receipts`, filters `no_visible_effect`, serializes it into the next model prompt, and does not mutate it while `model_call` is pending. `decisions` persists as an append-only record, but the relevant reads are the last decision's receipts and existing cover policy. `reusable_cover` carries at most the prior active action's `next_cover`; that is already an existing control/coverage path, not correction debt. `model_session_id` persists across turns within a session span, so persistent model-side context is a live uncertainty, not proof of no accumulation.

Candidate output: `{"candidate": "INELIGIBLE_FOR_THIS_CONTROLLER_PATH", "controller_sha256": "300ae84187c9fae70de9895e4a83197c64552601ff751ae5d05ed0f10809c322", "external_persistent_model_context": "UNINSPECTED", "negative_control": "PASS", "positive_control": "PASS"}`.

Independent AST/data-flow auditor output: `accumulator_mutations=[]`; positive and negative controls PASS; `effect_memory_writes_during_model_wait=0`; disposition `INELIGIBLE_FOR_THIS_CONTROLLER_PATH; external persistent model context remains uninspected`.

## Execution history / STOP preservation

The first harness attempt is retained as **STOP_HARNESS_DEFECT**, not a scientific result: PowerShell quoting broke the inline candidate program (`SyntaxError: '(' was never closed`), and the auditor incorrectly asserted the controller could not contain `--model` even though that string occurs in the external runner invocation. No candidate output was produced and no scientific claim was accepted from that attempt. The auditor assertion was corrected and the candidate was moved to a dedicated file; both final frozen programs then ran exactly once and passed. The initial failure is not erased or promoted to a result.

## Follow-up

Inspect the exact persistent runner (`research/doom/map01_persistent_model_runner_v2.py`) and any session persistence contract to determine whether accumulated correction intent can survive in external model context. Keep Issue #5791 open; do not implement anti-windup or request live T1 on the basis of this result. No GPU allocation or model call is justified by this static finding.
