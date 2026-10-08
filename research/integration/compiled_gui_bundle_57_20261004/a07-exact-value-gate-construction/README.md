# A07: exact-value gate construction check

**H:** a separately versioned compiled form method can prevent Submit when the observed field does not equal the task value, while retaining the two-step path when exact equality is observed.

**T:** execute the v2 adapter and compiled core with two source-pinned test-double sequences: (1) field pixels change but the value predicate remains false; (2) the exact-value predicate becomes true. **D:** scoped pass requires case 1 to stop after `enter_exact_token` with no Submit, and case 2 to permit Submit and complete only after a separate submission predicate. The saved raw outcome is independently audited by `audit.py`.

**C:** an existing model-authored graph or a task-specific verifier may supply the same guard without adopting another fixed adapter. **U:** the exact-value predicate is only as trustworthy as its observer; OCR/source-frame binding, false acceptance, model economics, and live application effects remain unmeasured.

Result: `PASS_EXACT_VALUE_GATE_CONSTRUCTION_SCOPED`. The wrong-value sequence stops as `SAFE_YIELD/effect_failed` after one transition; the exact-value sequence completes with two transitions. This is only a graph-contract construction check. `field_value_matches_task` is supplied by an observer and its real-world correctness is untested; no OCR, GUI, model/provider, input, network, or formal allocation ran. It does not qualify the v2 adapter for live use or establish an efficiency benefit.

Reproduce from the repository root:

```sh
python research/integration/compiled_gui_bundle_57_20261004/a07-exact-value-gate-construction/run.py /tmp/a07-raw.json
python research/integration/compiled_gui_bundle_57_20261004/a07-exact-value-gate-construction/audit.py /tmp/a07-raw.json /tmp/a07-audit.json
```
