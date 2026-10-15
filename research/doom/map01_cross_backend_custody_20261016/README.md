# MAP01: distinct-backend admission during unverified release

2026-10-16. Source main `026ce5e8ab0b466fbfb0dd2c0ec03e6c17f94169`.
**FAIL_SHARED_INPUT_CUSTODY** is the scientific outcome, not a test-run crash.
The finite Fake X characterization completed normally and under optimized Python.
There were no live GUI, game, model, WSL or container allocations.

## Question and frozen comparison

Does the #8960 backend-local custody fence prevent admission through a distinct
backend for the same underlying input domain? The original Executor runs one
5ms `a` hold. Fake X release-send is held until its failed/unverified terminal
has been published and the original Executor is closed. Keycode 38 remains down.
Attempt a second hold admission with the same target digest through three paths.

Alternate backends are constructed **before** the stall. The accepted-event sink
deliberately raises before `worker.start`, preserving the accepted intent but
never running another input/cleanup writer. Thus this measures constructor and
intent-admission custody, not completion of a second operation. All three cells
use the actual selected process-identity backend and ExecutorV13, with the
existing FakeDisplay/XTest fixture. `FREEZE.json` was written before the first run.

| Case | Original failure still retained / key held | Alternate accepted events | Alternate input emissions | Result |
|---|---|---|---|---|
| Same backend | Yes / 38 | 0 | 0 | Existing fence refuses with unverified release |
| Distinct backend, same session object | Yes / 38 | 1 | 0 | Shared-domain custody hypothesis fails |
| Distinct backend and session object, same fake display | Yes / 38 | 1 | 0 | Shared-domain custody hypothesis fails |

Each alternate worker remains unstarted and the gate remains closed at decision.
The new backend has its own empty obligation despite the original backend's
retained failed obligation. Normal and `-O` produce the same categorical result;
these are local construction repeats, not independent reliability samples.
After explicitly resuming each gate, the original owner retires and fake key
state becomes empty. Its earlier obligation remains unchanged; late cleanup is
not promoted to a recovery certificate.

## What changes next

Retain #8960's fence for its documented backend-object scope. Do not adopt it as
global/session/process single-writer custody or as a durable recovery mechanism.
In particular, wrapping a new backend or constructing a new session is not a
recovery operation. The original failure must remain owned outside any object
whose replacement can erase it.

The next integration needs an authority owner shared by every participating
input path for an identified backend/server incarnation, with original obligation
identity/deadline preserved, late-writer fencing and an explicit independently
verified release/recovery transition. A display-name dictionary or fresh wrapper
alone does not establish that domain, protect another process, or prevent display
restart/name reuse. Prefer connecting an existing caller/supervisor authority
once identified over adding a parallel global registry. Test both a refused
replacement while release is uncertain and healthy handoff after verified
release. Keep #59/#17 and the fail-closed recovery scope of #2437 open.

This experiment does not solve the native backend stall: an unresponsive input
transport still prevents a physical release-time bound. It does not test native
connections, process death/restart, recovery re-admission, window incarnation,
independent application effect or matched economics. The fake owners share one
FakeDisplay object; this is deliberate shared-state construction, not a claim
about separate real transport connections. Backend construction after the fault
is not qualified by these preconstructed-alternate cases.

## Reproduce locally

From the source-pinned repository with its selected backend and test dependencies
materialized (Python, Pillow, python-xlib; all display/input calls are patched):

```text
python research/doom/map01_cross_backend_custody_20261016/probe.py
python -O research/doom/map01_cross_backend_custody_20261016/probe.py
```

`need` checks remain active under `-O`. The last row reports completed
characterization separately from the scientific FAIL. Raw JSONL retains each
original obligation, both backend snapshots, acceptance, held state, send attempts
and late-return state. Empty stderr and original exit codes are retained in
`RUNS.json`. No source or outcome was changed after the first run.
