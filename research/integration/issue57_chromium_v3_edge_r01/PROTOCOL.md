# Issue #57 current-main Chromium / caller-v3 smoke R01

Pre-freeze construction probe: one successful submit completed before persistent
capture retention and a source manifest were added. It is excluded from R01
scoring because its raw PNG/POST/caller receipt were not retained. R01 below
is a fresh, single-use execution after the protocol, runner and auditor are
committed; the construction probe is not pooled or replayed as evidence.

## Question and scope

Does the current `adaptive_acquisition_caller_v3` plus
`integrated_efficiency_compiled_execution_v2` path complete one isolated,
headless Microsoft Edge form submission when exact visible text is checked by
Windows OCR, the compiled core admits one fresh observation, and a local HTTP
server independently checks the POST body?

This is a one-case adapter smoke, not a matched efficiency, reliability, MAP01,
or V5 target-generation experiment. The form starts with the exact task token
already present, so the only dispatched UI action is Submit. The model adapter
is an offline fixture. No external provider, user desktop, shared allocation,
Docker, WSLc, or network host is used; the HTTP server binds loopback only.

## Frozen procedure

- One fresh Edge process with a private temporary profile and headless mode.
- One localhost HTML form and one fixed token (`t991025-1`).
- Capture and OCR the visible form before dispatch and after submission.
- Use the current v3 caller and v2 compiled composition with one fresh action
  admission and the existing exact-token form method.
- Independently score the server's received POST body, preserve caller/model
  ledgers, compiled receipt, OCR observations and PNG captures.
- Close Edge, wait for process termination, remove only the test-owned profile,
  then record cleanup status.
- Run the saved-data auditor after the experiment. No retry, replacement,
  timing tuning, or reuse of a failed run as a passing run.

## Decision rule

Scoped `PASS` requires exactly one caller model attempt with its usage fields
retained, OCR exact-token state true on every accepted observation, one Submit
dispatch, one exact POST, caller task effect `succeeded`, compiled receipt
`TASK_SUCCEEDED` with one completed transition and verified neutral release,
all retained capture hashes matching, Edge close success, and removal of the
test-owned profile. Missing source/evidence/cleanup is `HOLD`; a complete
contradiction of task effect or release is `FAIL`.

Even a scoped pass proves no target-generation mutation, cold/warm comparison,
provider behavior, arbitrary task, persistent recovery, latency/token benefit,
or Research Preview readiness. The result cannot close #57.
