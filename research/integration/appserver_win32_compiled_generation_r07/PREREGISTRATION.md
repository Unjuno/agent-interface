# AppServer Win32 compiled generation run R07

## Question

Can a single real AppServer image-grounded decision be joined to the standard supervised Win32 public-MCP compiled caller while preserving the target generation across the provider wait, verifying input release, observing the resulting fixture state, and independently scoring the exact task effect?

## Frozen scope

- One current-authorized Windows workstation, one repository-owned `Agent Interface Win32 Fixture` process, one native HWND, and one 400x180 client region.
- One `gpt-6.1-sol` AppServer turn at low effort. The model sees the retained initial fixture screenshot and returns one integer point constrained to the client-region bounds in `conditions.json`.
- The caller uses the first standard public observation's `target_generation` as `expected_generation` for `run_public_compiled`. A later mismatch is a terminal failure with no dispatch.
- At most one compiled transition and one `interface_dispatch`. Its fixed program uses the model-selected point, types the harmless string `office`, sends Ctrl+S, and requires release of all input.
- The compiled postcondition reads the fixture effect file only after a fresh standard observation. `interface_verify_task` then runs one server-configured oracle bound to the exact action call ID and target generation.
- No WSLc or Docker use. No efficiency or reliability claim from one trial. No retry under this attempt ID.

## Outcomes and retention

The `run/` directory is exclusive and immutable once created. Provider failure, timeout, refusal, invalid coordinates, changed generation, uncertain dispatch, release failure, effect mismatch, or oracle failure remains the terminal result for R07. Raw provider protocol bytes and MCP request/response bytes are written by `ProviderAttemptRecorder`; the app-server protocol journal, standard receipts, fixture event/effect files, compiled receipt, and cleanup report are separately retained. `SHA256SUMS` is generated after cleanup. Any follow-up requires a new attempt ID and packet.

## Pass rule

All pass conditions in `conditions.json` must hold. Missing usage fields remain unavailable and fail the provider-accounting requirement. The internal compiled `TASK_SUCCEEDED` result is not the independent task score. Independent success requires both the fixture's exact saved effect and the server-configured oracle's verified receipt bound to the exact dispatch and target generation.

## Known limits

This is a scoped live Windows fixture experiment. It does not establish WSLc allocation eligibility, MAP01 control, recovery under blocked platform I/O, production-app correctness, matched efficiency, or a reliability rate.
