# Public guarded X11: blocking boundary remains open

2026-10-15, baseline main `a812e7881eba39c9f041ff11308853630b1fe8f1`.
Disposition: **BASELINE_BLOCKING_REPRODUCED_PUBLIC_PATH**. The auditor's
`PASS_CHARACTERIZATION_NOT_RELEASE_BOUND` means the characterization is
consistent, not that bounded release has been achieved.

The frozen probe calls the actual `dispatch_in_session` →
`X11RuntimeSession.dispatch` → `_GuardedBackend`/`X11Backend.execute` and
`release_all`. Core admission and result/recovery accounting execute normally.
The guarded owner, focus observation, native preflight, keyboard mapping and X
connection are doubles. `NativeHandleBridge._run_guarded`, image/target binding,
and cancellation are not exercised. No real display connection is opened.

| Case | At the blocked boundary, fake clock at original expiry | After unblocking |
|---|---|---|
| Healthy control | No block | Public result completed, verified-empty fake release |
| Second key's focus query | CTRL remains down; worker blocked; no dispatch result | Following `a` press refused by the deadline fence; execution_failed with verified cleanup |
| Cleanup sync | Fake bitmap already empty; worker blocked; no dispatch result | execution_failed with verified cleanup after sync returns |

Both ordinary and optimized Python produced these three outcomes. The raw-only
auditor checked 26 conditions and rejected four separate mutations in each mode:
erasing held CTRL at the focus block, fabricating a returned receipt at the sync
block, adding a late `a` press, and fabricating verified cleanup. `normal.json`
and `optimized.json` retain full programs, emissions, boundary snapshots and
public results; adjacent audit files bind their SHA256 values. The pre-run
freeze covers 166 source/plan files from this materialized checkout, including
the probe, auditor and runtime sources. It is not a claim that every repository
file or every platform path executed. A final postcheck confirms these frozen
files remained unchanged.

The memory-only bitmap distinguishes emitted cleanup from completed readback.
It is not independent OS/application evidence. Reaching the original expiry in
a fake clock, while a known Event blocks the worker, proves the lack of progress
in this schedule; the five-second harness caps are not a measured or enforced
physical release bound. No actual cancellation is requested, and no cancel
result should be inferred from the expiry cases.

## Decision and next action

Keep #17 and #2's backend fault-boundary risk open. The late-new-press fence
shipped in #8927 remains useful after a query returns, but cannot release the
held prefix while that query is blocked. Do not substitute another expiry check
or a bounded caller response for release progress.

The next repair must give revocation/cleanup a path that does not wait on the
blocked observation, while retaining one serialized input authority and fencing
late observation replies before new input. Exercise the same two boundaries,
explicit cancellation, duplicate cancellation, late replies and uncertain
readback against that candidate. A separate uncoordinated X connection is not
an established solution. Even a candidate passing Fake X must then qualify its
real transport/backend ordering, independent release evidence, finite recovery
and task effect on a fresh permitted live attempt. No live allocation, GUI,
model, WSLc/Docker invocation, physical input or MAP01 result was added here.

## Reproduction

Use a fresh output name; the tools refuse to overwrite retained results. A
reproduction must use the pinned source hashes (or be labelled a changed-source
construction), and no formal/live allocation is replayed:

```sh
python -B probe.py --output REPRO.json
python -B audit.py REPRO.json --output REPRO_AUDIT.json
```

Run from this directory with the repository root on `PYTHONPATH`. The default
`SOURCE_FREEZE.json` is checked before any probe case. The auditor imports only
standard-library modules and never invokes the runtime or collector.
