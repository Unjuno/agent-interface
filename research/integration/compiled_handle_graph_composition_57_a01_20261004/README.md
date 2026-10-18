# Compiled form graph × pixel-handle composition (A01)

## Question and scope

Can the current-main compiled GUI state machine consume the A03 bounded field crop and A02 submit patch as session target handles, revalidate each action at admission, and fail closed when those pixels change between observation and admission?

This is an offline integration construction using five retained screenshots. The field region and submit region are actual pixel handles; the compiled v2 graph and compiled GUI runtime are the frozen source modules. Observation, admission, execution, exact-value recognition, submission-effect recognition, and release records are test doubles. No GUI, model, OCR, keyboard, pointer, network, or task was operated. Results cannot establish target semantics, application effect, useful feedback, latency/token efficiency, or real input authority.

## H/T/D/C/U frozen before candidate run

- **H:** In this offline test-double composition, five retained screenshot cases complete the two-action compiled form graph when handle pixels remain stable. If the field patch is replaced between observation and first admission, the graph dispatches zero actions. If the submit patch is replaced between observation and second admission, the first test-double operation remains recorded but Submit is never dispatched.
- **T:** One construction run over all five frozen A02/A03 screenshots, with baseline, field-race, and submit-race conditions per screenshot. Use current-main `runtime/core_v1/compiled_gui.py`, current-main handle modules, A03's bounded-box function, and PR #7353's exact compiled form adapter. Candidate output is retained once; a separate auditor derives all scenario outcomes from raw receipts. No retries or changed thresholds.
- **D:** PASS only for 5/5 baseline two-operation `TASK_SUCCEEDED` receipts, 5/5 field-race refusals before any execute, 5/5 submit-race refusals after exactly one `enter_exact_token` operation and before any `activate_submit`, and no failed/held-input release receipts. Any mismatch is FAIL; missing/invalid raw is HOLD.
- **C:** Exact pixel identity can persist at a geometrically plausible but semantically wrong patch. A14's task-3 visual-review text claims the field and Save button are absent, but the retained screenshot visibly shows both; task 3 therefore is not an absence control. Positive semantic/effect predicates are supplied by a test double.
- **U:** The retained captures are from earlier fixture/model work and are not fresh GUI captures. No container run occurred because the current OrbStack daemon previously returned an unsupported content-blob error; this is a native macOS construction only. Pillow, the clock, pixels, observation meaning, authorization, execution, effect, and release all run in-process. No live safety, semantic grounding, task correctness, speed, token, or end-to-end benefit claim follows.

## Frozen inputs and source identities

`FREEZE.json` pins the current-main base and module blob IDs, source PR heads and adapter blob, A02/A03 input manifests and retained PNG SHA-256 values, Pillow version, command, conditions, and decision gate. `source/a03_candidate.py` and `source/compiled_form_adapter_v2.py` preserve the exact upstream sources used. `inputs/` contains the screenshot bytes and source manifests.

## Reproduction

From the repository root, with Python 3.12 and Pillow installed:

```sh
python3.12 research/integration/compiled_handle_graph_composition_57_a01_20261004/run.py > research/integration/compiled_handle_graph_composition_57_a01_20261004/out/candidate.json
python3.12 research/integration/compiled_handle_graph_composition_57_a01_20261004/audit.py research/integration/compiled_handle_graph_composition_57_a01_20261004/out/candidate.json
```

The recorded execution used the same candidate command through `uv run --python 3.12 --with pillow`. This native run is not represented as a container execution.

## Result and disposition

See `out/candidate.json`, `out/audit.json`, and `SHA256SUMS`. Keep the conclusion limited to composition of the supplied modules and synthetic adapters. Overall #57 integrated efficiency remains HOLD pending live same-task, same-model effect and end-to-end resource measurement.
