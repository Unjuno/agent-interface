# Compiled execution through the adaptive v3 caller

Use `integrated_efficiency_compiled_execution_v2.py` for the explicit v3
composition. Legacy `integrated_efficiency_compiled_execution_v1.py` retains its
v2 contract; old frozen sources/results are not migrated by importing this file.

```python
from research.live_control.integrated_efficiency_compiled_execution_v2 import (
    run_compiled_interface_in_caller,
)

result = run_compiled_interface_in_caller(
    v3_spec, caller_adapters, interface_for_target, execution_adapters,
    on_receipt=retain_compiled_receipt,
)
```

The names in this example are caller-owned inputs/adapters, not a runnable live
allocation. The v3 specification includes `local_repair_on`, and model results
include the v3 image/wait accounting fields. Actual model calls inside adapters
also need the shared ledger; this entry does not discover hidden calls.

`interface_for_target(payload)` is required and is called after final caller
revalidation. Its detached payload contains the final `target` and `check`.
Construct the compiled interface from that target, including current domain
references/session scope. The callback is trusted construction, not a grant of
input authority or an independent proof that its mapping is correct. The core's
per-action observation/admission adapters still validate actual references,
scope, generation, deadline and release. A static interface object is rejected;
the helper does not silently ignore an updated final target.

The result keeps the caller's outer outcome and adds:

- `compiled_execution_receipt`: a detached returned core receipt, or null if
  the core never returned one. Core method completion is separate from the
  caller's independent task-effect verdict.
- `compiled_receipt_publication_error`: the original sink error's type and
  diagnostic, or null. This is in-memory evidence, not durable publication.

The receipt sink receives another copy before outer verification. Mutation
cannot change the retained receipt or execution decision. If it raises an
ordinary Exception after a returned core receipt, the helper raises the caller's
typed `ExecutionReceiptError` from the original error. The caller captures its
validated, detached execution progress before failure clock/journal callbacks.
The result remains CALLER_FAILED, skips outer effect verification, and retains
known input delivery/progress. Only trusted execute adapters may supply this
exception; similarly named attributes on ordinary errors are ignored.

Runtime failure retains the completed prefix as `safe_yield/execution_failed`.
An unverified current input remains `delivery_uncertain` even with an already
completed prefix. Explicit no-input refusal differs from missing delivery
evidence; neither missing metadata nor zero completed transitions proves that
input was not attempted. Nothing is automatically replayed or recovered.

If the core raises before returning a receipt, the helper leaves the receipt and
progress unknown rather than reconstructing a prefix. Non-Exception stops
propagate unchanged. This entry does not interrupt blocked callbacks, guarantee
physical release time, retain evidence across process death, or verify app
effects. Qualify the actual domain mapping, live telemetry, effect/collateral
predicates and recovery separately before a frozen matched comparison.

[Source-bound local repair evidence](../integration/compiled_caller_v3_repair_20261016/README.md)
includes target promotion, a real model/planner/caller/core chain with inert RPC
and input/effect adapters, and legacy/mutation controls. It is not a live task,
provider or economics result.

For the exact-value form, the [guarded-admission compatibility repair](../integration/compiled_form_guarded_admission_20261016/README.md)
keeps field identity separate from its post-entry value effect. Submit retains
the exact-value dependency. Actual guarded-adapter/memory-bridge tests cover
that distinction; they do not qualify the full native domain path.
