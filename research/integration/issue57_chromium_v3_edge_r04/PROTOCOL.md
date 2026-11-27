# Issue #57 current-main Chromium / caller-v3 smoke R04

R01 and R02 stopped before Edge or OCR. R03 completed the isolated action,
exact local POST, receipt and cleanup checks, but its auditor returned HOLD
because it incorrectly required the field token to remain OCR-visible after
the form had submitted. The R03 data and disposition remain unchanged. R04
retains the same task and scope while correcting the preregistered observation
predicate by stage; it uses a fresh token and a new output directory.

## Question and scope

Does the current `adaptive_acquisition_caller_v3` plus
`integrated_efficiency_compiled_execution_v2` path complete one isolated,
headless Microsoft Edge form submission when exact visible text is checked by
Windows OCR before Submit, and a loopback HTTP server independently checks the
POST body?

This is a one-case adapter smoke, not a matched efficiency, reliability, MAP01,
or V5 target-generation experiment. The form starts with the exact task token
already present, so the only dispatched UI action is Submit. The model adapter
is an offline fixture. No external provider, user desktop, shared allocation,
Docker, WSLc, or non-loopback host is used; the HTTP server binds loopback only.

## Frozen procedure and gate

- Before Edge starts, verify the Git root, clean source state, all frozen source
  paths, protocol/auditor paths, and source hashes.
- One fresh Edge process with a private temporary profile and headless mode.
- One localhost HTML form and one fixed token (`t991025-2`).
- Require exact-token OCR in the pre-action `verify_value` observation.
- After Submit, require a fresh `submitted` observation with
  `submission_pixels_changed=true`; OCR of the removed form is not a gate.
- Use the current v3 caller and v2 compiled composition with one fresh action
  admission and the exact-token form method.
- Independently score the server's received POST body, preserve caller/model
  ledgers, compiled receipt, OCR observations and PNG captures.
- Close Edge, wait for process termination, remove only the test-owned profile,
  then record cleanup status.
- Run the saved-data auditor after the experiment. No retry, replacement,
  timing tuning, or reuse of a failed run as a passing run.

Scoped `PASS` requires all conditions above, exactly one caller model attempt
with complete usage/accounting metadata, exactly one Submit and exact POST,
caller task effect `succeeded`, compiled receipt `TASK_SUCCEEDED` with one
completed transition and verified release, matching capture hashes, Edge
closure and profile cleanup. Missing evidence or cleanup is `HOLD`; a complete
contradiction of task effect or release is `FAIL`.

Even a scoped pass proves no target-generation mutation, two-action entry,
cold/warm comparison, provider behavior, arbitrary task, persistent recovery,
latency/token benefit, or Research Preview readiness. The result cannot close
#57.
