# Golden-v3 task and cleanup result semantics — R01

Source: exact merged main `dd206c8e52571131e01d4f99cd75e9c5d2e43a5e`.

The focused golden-v3 suite passed 13/13 in normal Python and 13/13 under `-O`. The deterministic adapter probe supplied `program_completed=true`, `task_success=true`, `effect_status=confirmed`, plus `cleanup_error="release readback failed"`. The public envelope returned `status=cleanup_failed`, `program_completed=true`, and top-level `task_success=false`, while `raw_dispatch.result.task_success=true` and the cleanup error remained visible.

The behavior is explicitly covered by `test_cleanup_failure_cannot_succeed`; this is current fail-closed contract behavior, not a newly found implementation defect. It exposes two meanings: the raw application/task assertion and the top-level qualified outcome after cleanup. Consumers must retain both. Whether the product should name the application assertion separately in the public schema is a contract decision; this packet does not recommend changing the contract or declare the task successful.

No live control, physical release, delayed-input exclusion, MAP01, matched efficiency, reliability rate, or preview acceptance was tested.
