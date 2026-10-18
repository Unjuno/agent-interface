# A08: cancellation callback exception after released input

**H:** a cancellation callback that becomes unavailable after an input terminal should stop further input while still returning a typed receipt for the completed prefix.

**T:** source-load `CompiledExecution._cancelled` from the retained exact adapter source `ADAPTER_PINNED.py` (PR #7443 commit `6144a1b0a2c88f5d88ff1fce148381f1f22269e1`), compose it with the pinned current core, and have the callback return `False` for the first three checks then raise at check four. The first three checks cover loop entry, pre-action, and post-admission; check four happens after the first action terminal/release. No image/OCR or GUI adapter is called.

**D:** `PASS_CALLBACK_FAILURE_RETAINED` only if the first action's verified release is preserved, no second input is dispatched, and a typed yield receipt returns. **C:** the adapter's private event list records `action_terminal`, but that is not returned as the public run result when the exception escapes. An outer caller might catch the exception, but its behavior is outside this adapter/core contract.

Result: `FAIL_CALLBACK_EXCEPTION_DROPS_TYPED_RECEIPT`. The entry operation executed and its terminal event verified all keys/buttons released; the next cancellation check raised `RuntimeError`, and no receipt returned. This is a source-pinned test-double counterexample, not a live GUI or safety incident. No code in PR #7443 was modified. A robust fix should turn cancellation-source failure into a typed fail-closed yield while preserving the completed prefix, with a post-action exception regression.

**U:** no live app, owner-thread lifecycle, caller exception policy, or provider/model was exercised. No formal allocation or runtime environment was used.

Reproduce from repository root:

```sh
python research/integration/compiled_gui_bundle_57_20261004/a08-cancellation-callback-exception/run.py research/integration/compiled_gui_bundle_57_20261004/a08-cancellation-callback-exception/RAW.json
python research/integration/compiled_gui_bundle_57_20261004/a08-cancellation-callback-exception/audit.py research/integration/compiled_gui_bundle_57_20261004/a08-cancellation-callback-exception/RAW.json research/integration/compiled_gui_bundle_57_20261004/a08-cancellation-callback-exception/AUDIT.json
```
