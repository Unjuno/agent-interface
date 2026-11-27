# Current V39 cancellation / recovered-source composition

Base `35a137b4943eac1b44aac58b2d540ed2e7ff9173`; tested code
`0e3481c2d375e3d849f91d9e27858308347c93fb`. New ordinary regression:
`research/doom/test_map01_v39_cancel_recovery_composition.py`. No production
behavior change and no historical PR8792 producer replay.

The selected three modules pass **44 unique methods**, zero failures/errors/
skips, normal and actual optimized Python. Three new methods retain ten rows:
health/ammo hard crossing and recovery for cancelled/completed/expired terminals
(six), unverified release/held key/cancel-write failure (three), and a clean
no-invalidation planner result (one). Current controller/guard/cancel/final-
admission functions run directly; the exact nested production wait AST runs
with a synthetic queue and recording in-memory process/planner callbacks.

Both typed and full recovered observations arrive during cancel wait. Local
planner invalidation precedes cancel write/flush and interrupt. The old monitor
stays inactive; the wait retains the latest full frame at sequence12. A new
monitor can seed health96/ammo4 from it, while a deliberately completed and
still-eligible old planner answer remains REJECTED_POLICY_INVALIDATED with no
Executor/input authority. A clean new result reaches only action validity,
not input admission. Failed closure/write retains conservative physical state,
recovery-required/no-authority evidence and aborts the planner. Post-failure
final/monitor calls in tests are explicit no-input counterprobes, not an
application continuation or permission to resume after failed cleanup.

A complete copied-controller directed control drops only the original
invalidation argument at final admission. Nine subtest assertions fail per
mode (three methods, zero errors/skips); all old results then wrongly reach
READY_FOR_ACTION_VALIDITY. The saved-only reader imports no candidate and checks
order, refusal, latest full frame, new monitor seed, closure/failure receipts,
positive control and method/optimization accounting. It rejects six copied
contradictions per mode. Raw rows, all streams/process receipts,31 executed
repository Python source joins, mutation expression/source and inert runners
are retained. Source joins are the loaded repository selection, not every
platform/dependency or complete main-loop execution.

## Retained setup failures

Initial fixture tests omitted the current owner_release event, keys_unknown
and key_state_errors fields: six expected-positive rows refused and the
cancel-write case escaped OSError beyond the fixture's RuntimeError catch.
Original test source/full streams remain. This was fixture mismatch, not a
production defect. The corrected fixture uses the actual current release
shape and retains ordinary exception evidence. No runtime contract weakened.

The first isolated collection then failed before tests because NumPy existed
only in user site-packages. Full import stderr/process receipt remain in
initial-import. NumPy2.3.4 (the same installed user-site version) was installed
into the dedicated test environment; final isolated runs use it and Pillow
12.2.0. These dependency versions were confirmed after the run. This was an
ordinary local dependency repair, not a live allocation/retry. Initial and
corrected local test outputs are not independent scientific trials.

## Limits / next gate

Synthetic typed values are not image recognition; queued event order is chosen.
Fixture empty release is not physical input proof or a blocked-I/O time bound.
The exact wait AST plus current helper calls does not run full main, real
Executor/OS, transport or planner/model; no actual task effect, live recovery,
matched token/latency or transfer result is established. No GUI/game/native
input/model/provider/WSL/container/allocation ran. Keep #59/#57/#17 open.

This replaces historical-source inference with a new current-function
qualification. Next work must connect the same retained invalidation and fresh
full observation across the actual controller/Executor transport, then measure
independent release and task effects in a permitted fresh live allocation.
