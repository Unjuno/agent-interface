# Issue #4485 allocation v2 — retained audit STOP

## Decision

`STOP_AUDIT_IMPLEMENTATION_MISMATCH`. The formal seven-case matrix completed
inside the frozen OrbStack container and its fake executable was reached, but
the frozen independent auditor returned one provenance error. Under the
predeclared D gate this allocation has no formal scientific PASS/FAIL decision.

## Formal observations from retained raw

- `exit0`: fake invocation=1; broker receipt says child `returncode: 0`; broker
  process exits 1. This is the hypothesized counterexample, retained as a raw
  observation only because the audit gate did not pass.
- `exit23`: fake invocation=1; receipt and broker process both return 23.
- `timeout`: fake invocation=1; receipt is typed
  `HOST_BROKER_SUBPROCESS_TIMEOUT`, returncode null; broker exits 1.
- `unavailable`: fake invocation=0 by design; receipt is typed
  `HOST_BROKER_EXECUTABLE_UNAVAILABLE`, returncode null; broker exits 1.
- `malformed`: process exits 1 with `KeyError: 'schema'`; no receipt/response.
- `one-shot-idle`: no request or fake call; `--once` remains idle until the
  300 ms outer bound, which terminates the process with -9.
- `two-queued`: fake invocation=1; exactly one response and receipt for
  `queued-a`; `queued-b` remains queued; broker exits 1 because its first child
  returns 0.

## Auditor STOP cause

`FREEZE.json` preregisters `timeout_case.fake_sleep_s = 2.0`. The retained raw
`timeout/invocation-01.json` records `sleep_s = 2.0`. The frozen auditor instead
hardcodes an expected value of `0.3`, so its only error is
`timeout: expected recorded sleeping fake invocation`. It reports
`contract_errors=0`, but this auditor implementation mismatch prevents the
predeclared audit gate from passing.

The formal run and audit outputs are immutable under `formal_run_01/`; neither
is rerun or edited. Issue #4485 records the STOP, and a separate successor
Issue will authorize a fresh raw-only audit implementation against these bytes.

## Scope

This does not authorize a shared broker code change and does not establish model
utility, GUI/task success, efficiency, Docker Desktop equivalence, or a product
claim.
