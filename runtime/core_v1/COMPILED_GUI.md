# Bounded compiled GUI continuation

The portable Python runtime includes the existing research state graph at
`runtime.core_v1.compiled_gui`. `research/live_control/compiled_gui_interface_v1.py`
is a compatibility import of the same `validate` and `run` implementation.
The shared implementation neither imports research modules nor opens a display.

The caller authors the bounded interface and supplies synchronous `observe`,
`admit`, `execute`, `verify_effect`, `cancelled` and optional `journal` adapters.
Observations select a declared branch. Each action requires a fresh admission,
verified neutral release, then new evidence and an effect verdict before the
next branch. Unknown/ambiguous states, missing or stale symbols, unavailable
or failed effects, uncertain input and exhausted budgets yield with their
completed prefix. Symbols do not grant authority or contain executable points.
Raw evidence and receipt persistence remain the adapters' responsibility.

Each observation request receives its own declared-predicate list. The journal
receives a separate deep copy of each event, so callback-local formatting or
later edits to retained payloads cannot change private declarations or returned
critical evidence. Callbacks remain trusted synchronous code: their exceptions
propagate and their I/O must obey the existing deadline contract.

After observation, branch journaling, admission, effect verification and returned
execution, the runtime rechecks its original method deadline. Reaching the exact
deadline counts as exhaustion. A late observation is retained, but cannot admit
new input or complete the method. A late completed execution retains its
transition and pending effect before yielding. Release failure and uncertain
delivery remain explicit rather than being hidden by a budget outcome.

The executor receives `valid_until_ns=min(admission_deadline,method_deadline)`.
All deadlines and the injected `clock` must share one monotonic clock domain.
Adapters must honor that deadline for I/O and each new input. These checks only
operate when a synchronous call returns; they cannot preempt a blocked adapter,
undo emitted input, guarantee physical release by a deadline, or implement hard
real-time control. No automatic replay, repair, grounding or local model exists.

`TASK_SUCCEEDED` is the graph's adapter/predicate verdict, not an independent
application effect certificate. A form's changed pixels do not verify its text.
Independent task/collateral scoring and primary image review remain required
for acceptance. Historical frozen live results keep their original sources.
New live source manifests must pin this shared module as well as any research
compatibility wrapper used by the caller.
Packaging and boundary tests establish availability and stopping behavior,
not fewer model resumptions in a live product, speed, token savings or human
performance. The previous primary six-task comparison remains efficiency HOLD.

Validation uses `runtime.core_v1.test_compiled_gui` and
`runtime.distribution_v2.test_compiled_archive` in the shared local/CI native runner.
The isolated archive test uses an explicit working-source snapshot without Git;
release builds continue to pin committed HEAD through the normal builder.

On the guarded Python X11 path, pass `valid_until_ns` as the bridge action's
`expires_at_ns`. The bridge clamps its existing five-second cap rather than
renewing the outer method budget. This argument must use the execution host's
monotonic clock. The deadline bridge alone does not supply perception, effect verification
or independent task scoring.

The opt-in shared X11 Python adapter now supplies this connection:
[`runtime.guarded_x11_v1.compiled`](../guarded_x11_v1/COMPILED.md).
It uses the existing graph with fresh bridge captures, boolean target prerequisites,
caller-owned perception/effect callbacks, per-action revalidation, one-use
admission tokens and retained raw receipts. Its application-specific primary
live trial does not establish general text verification or efficiency gains.
