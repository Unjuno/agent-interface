# R04 disposition

The frozen R04 run started its private Edge session and retained the initial
PNG. The caller completed one offline model-fixture attempt, but the compiled
core returned `RUNTIME_FAILED / observation_failed` with zero observations and
zero transitions. The outer caller returned
`EXECUTION_INCOMPLETE / execution_failed`, `input_dispatched=false`, and
`delivery=not_attempted`; no Submit callback or POST was reached. Edge exited
0 and the private profile/temp root were removed. The pre-action screen can be
re-read from `raw/frame-1.png`; Windows OCR on that retained image returned
`t991025-2 Save` and exact-token state true. This re-read is diagnostic only,
not a substitute for the missing original runtime observation receipt.

The test assertion failed before it serialized `run.json`, so R04 is incomplete
evidence and `HOLD`; the precise observer exception was not retained. Conditions,
the first capture, and cleanup are preserved. No input was sent. Do not rerun
R04 or infer that the R03 positive establishes repeatability. A future run
requires a pre-action diagnostic wrapper that persists observer exceptions and
complete result envelopes before assertions.

The frozen conditions file also retained the prior token value (`t991025-1`)
while the source/test page used `t991025-2`; the retained PNG and source hash
identify the actual page token. This manifest mismatch independently keeps
R04 on HOLD.
