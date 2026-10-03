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

In the declared shared monotonic clock domain, a capture cannot be later than
the return of its observation adapter. Evidence for a pending effect must also
be captured at or after the preceding execution adapter returned. An inconsistent
capture yields `stale_observation` before verification, another action or method
completion, retaining the completed prefix and pending effect. Equal timestamps
are allowed for clock quantization. An initial capture may precede method start;
admission still owns its freshness/target checks. These ordering checks do not
authenticate capture timestamps, establish clock-domain provenance, or certify
application effects.

Each returned effect-verdict dictionary is copied after exact-shape validation
and before checking its status and successful evidence reference. A later journal
callback cannot rebind those fields through its retained return object. This is
dictionary custody; failed/unavailable references are not generally scalar-type
validated, and copying does not authenticate a witness or physical task effect.

Cancellation is cooperative: the runtime consults the adapter at loop entry and
before admitting or dispatching another action. The final completion branch does
not poll again after its observation, effect verification or branch journal.
Cancellation latched there can therefore coexist with `TASK_SUCCEEDED` when no
further input is required. This is the existing policy for checking cancellation,
not a guarantee that cancellation wins until the terminal receipt. A caller needing that stronger
termination policy must qualify it separately; completed effects are not undone.

An admission return is copied after exact builtin-dictionary field validation
and before eligibility/freshness checks. Accepted fields are builtin scalars;
later callback-local edits to the returned dictionary cannot rebind the checked
authorization, sequence or deadline sent to the executor. Actual cancellation
and downstream authorization checks remain required. This snapshot does not
provide live revocation, custom-object or concurrent-callback safety.

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

Successful effect verdicts require an exact-string, nonempty `evidence_ref`
of at most 64 characters, matching the existing reference bound. A separate
verifier witness is permitted; the reference need not equal the observation's
reference. Malformed success metadata raises `ValueError` before the next
branch or final completion, with prior action/journal evidence retained.
Failed or unavailable verdicts keep their safe-yield behavior when the
reference is absent. This syntax check does not verify the witness's existence
or authenticity.

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

An execution-terminal dictionary is copied after its exact outer shape and
optional dispatch flag are checked. Release neutrality and an explicitly
attested pre-input refusal are evaluated before the `action_terminal` journal
callback. Later edits to an executor-retained dictionary or held-input lists
cannot promote uncertain delivery, erase a completed prefix, replace action or
effect references, or downgrade originally reported input to a pre-input refusal.
The copy preserves original field types; it does not invoke terminal-member
copy hooks to convert malformed release or reference objects into valid values.
These retained declarations do not authenticate executor truth or physical input
release. Actual cancellation remains the separate cooperative callback check.


Nested release containers must be exact built-in lists. After execute returns,
any other container stops with RUNTIME_FAILED/execution_failed without invoking
its equality, length, iteration or copy hooks. Verified completed transitions
are preserved; the malformed return does not become a completed transition or
a pre-input refusal. An action_terminal event records invalid_release with
release_verified=false. The receipt additionally carries unresolved_execution
only for this rejection: action, malformed_release_container reason, false
release_verified, the returned strict input_dispatched flag or null, and bounded
exact-string action/effect references or null. Opaque references are omitted.

Those fields preserve adapter declarations for external reconciliation. They
do not prove input delivery, physical neutrality or effect authenticity. The
caller must stop, establish input safety using an authorized backend and check
actual effects before choosing a new operation; RUNTIME_FAILED grants no replay
permission. This path does not clean up input, retry, resume or provide durable
recovery. Existing pending_effect semantics are unchanged. Other malformed
terminal fields retain their original validation behavior; arbitrary objects
and concurrent callback mutation remain outside the qualified scope. Exact
built-in-list paths keep their prior receipt shape and behavior.

The execution-finished clock sample occurs after local terminal validation and
the retained release/pre-input-refusal decisions, before the journal callback.
Thus a supplied synchronous clock callback cannot rewrite the execution return
used for those decisions. The later sample is a conservative lower bound for
subsequent effect observations in the declared monotonic clock domain: an older
capture may be rejected even if the physical effect had already happened.
This does not authenticate the clock, impose a hard deadline, or make callback
execution concurrent or durable. Malformed returns that stop or raise during
local validation do not require an execution-finished clock sample.

Returned observations are validated and copied before the supplied observation
clock callback. Later callback edits cannot rebind the retained predicates or
capture metadata used for branch selection and effect verification. The upper
capture bound is sampled after local validation, so it is a consistency check
against that sample rather than an authenticated instant of adapter return.
Malformed observations keep their existing refusal/validation semantics; a
validation exception can occur before the clock callback is invoked.
