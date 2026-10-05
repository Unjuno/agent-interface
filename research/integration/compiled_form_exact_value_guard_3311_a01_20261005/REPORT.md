# Compiled-form exact-value guard differential — Issue #3311

**Experiment:** `compiled-form-guard-differential-3311-20261005-01`
**Executed source:** `Unjuno/agent-interface` `main` at `33f354c27408bce88abb705397b3e260eb2faa51`. At packaging, current `main` is `3f24e85bff32a93fbc1ca244f7f249b843710743`; all four relevant source/test blob IDs match the checks below. The current v2 regression suite was run at its parent `21e55a7179adc0c41a1bfd31cc4f2c0fbb14c2ab` (5/5); the test and runtime blobs are identical at the packaging head.
**Disposition:** `PASS_DIFFERENTIAL_GUARD` for the synthetic runtime branch contrast; no live desktop or efficiency disposition.

## H/T/D/C/U

- **H:** Under identical synthetic evidence where a form field's pixels changed but the observed value did not equal the task value, compiled method v1 may submit and report runtime completion because it guards on pixel change; v2 should yield before Submit because it requires exact value match and a present Submit target.
- **T:** Run both current-main adapters against the same three synthetic observation rows, same compiled runtime, and the same one-use admission/execution/effect callbacks. Project only predicates declared by each interface. Stop after this one deterministic contrast; run the existing focused v2 regression suite as a separate construction check.
- **D:** PASS only if v1 emits `enter_exact_token` then `activate_submit`, while v2 emits only `enter_exact_token` and returns `SAFE_YIELD` on the second observation. Otherwise FAIL. The runtime terminal outcome is not treated as independently scored task success.
- **C:** A v1 false positive can be caught at the final task boundary only if the independent application scorer rejects the wrong value. V1 cannot consume the exact-value predicate because it is undeclared; the harness filters the same underlying rows to each interface's declared predicates. This tests adapter/runtime semantics, not perception quality.
- **U:** One synthetic sequence; no population estimate. Exact-value truth was supplied by the harness, not OCR or an application. No live app, model, GUI, host IPC, user input, repair loop, token, latency, cost, or efficiency was measured. The outcome supports considering v2 in a future frozen composition and retaining independent scoring.

## Result

On the same synthetic rows, v1 submitted after `field_pixels_changed=true` while `field_value_matches_task=false`; its compiled runtime terminal was `TASK_SUCCEEDED` from the synthetic `submission_pixels_changed` predicate. V2 made no Submit action and yielded `SAFE_YIELD / effect_failed` after that wrong-value observation. Both executed action receipts had verified key/button release. The independent raw audit reconstructed these differences from `raw-differential.json` and passed.

The current v2 regression suite passed **5/5** at parent commit `21e55a7179adc0c41a1bfd31cc4f2c0fbb14c2ab`, including the disappearing-Submit-target refusal control; its relevant source/test blobs are identical on packaging commit `3f24e85bff32a93fbc1ca244f7f249b843710743`. An earlier four-test run at the original experiment head is retained separately. This does not validate v2's observer on a live surface, integrate v2 into the frozen three-arm plan, or permit editing/restarting the one-shot #3489 allocation. A future formal comparison would need a prospective source/schema manifest for the exact-value predicate and the matched independent scorer.

## Commands and environment

- Differential run: `python3 work/current-main-compiled-form-guard-20261005/run_differential.py`
- Focused regression suite: `PYTHONPATH=work/current-main-compiled-form-guard-20261005 python3 -m unittest research.live_control.test_integrated_efficiency_compiled_adapter_v2 -v`
- Raw audit: `python3 work/current-main-compiled-form-guard-20261005/audit_raw.py`
- Host: macOS 27.0.1, Darwin arm64, Python 3.14.5. No container/image or live allocation was used.

## Provenance

The experiment harness and source files were materialized from commit `33f354c27408bce88abb705397b3e260eb2faa51`. Latest `main` at packaging is `3f24e85bff32a93fbc1ca244f7f249b843710743`. The v1/v2 adapters and compiled runtime match the tested source blobs; the focused v2 test blob is `277ce05d9583ae4172ce86663d150a705eb9bb22`. Git blob IDs:

- v1 adapter: `22a15b10c2bc1b4f0d04ed1eb189a97983b3c60d`
- v2 adapter: `e88409619f943086d877dc5b741e141075e2f403`
- compiled runtime: `93aeff9307143e996ca638e0dd0646290e289763`
- v2 regression test: `277ce05d9583ae4172ce86663d150a705eb9bb22`

To reproduce without overwriting retained evidence, copy `executed-runner.py` into a fresh temporary directory and run that copy with the full repository root on `PYTHONPATH`; the runner writes `raw-differential.json` beside itself. `audit_raw.py` independently checks the preserved raw branch/action/outcome and release events. `test-output-main-21e55.txt` preserves the latest focused suite output; `test-output-main-33f.txt` retains the earlier four-test run. A pre-run harness attempt that violated the runtime's declared-predicate contract and an initial audit-field-name assertion error are preserved in `construction-attempts.txt`; neither issued model, GUI or native input.
