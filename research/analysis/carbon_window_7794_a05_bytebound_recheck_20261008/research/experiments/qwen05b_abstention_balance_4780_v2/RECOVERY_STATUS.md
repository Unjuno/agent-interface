# Recovery status — Issue #5014 v2 frozen package and resource HOLD

Exact-content archive of the 23-file remote package from branch
`research/qwen05b-abstention-balance-4780-20260928-v2`. It preserves the v2
freeze, protocol, inputs, source, pre-fit receipt, and `RESOURCE_HOLD.md`.

The pre-fit receipt reports 8/8 CPU protocol/schema tests and `PREFLIGHT_OK`,
but formal fit invocations = 0 and no model/GPU run. This is not a LoRA result
or a lease. The resource note records `HOLD_RESOURCE_OWNERSHIP`; the later
Issue #5014 checkpoint (2026-10-01) says the published v2 freeze is stale
against current main and requires fresh provenance plus coordinator-confirmed
exclusive arbitration before any fit. Preserve the allocation/history, but do
not inherit the slot, launch, refreeze in place, or infer permission from an
idle-GPU snapshot. Any future run is a separately authorized current-main
allocation.

Recovery performed no training, model load, CUDA call, Docker invocation, or
formal/audit execution.
