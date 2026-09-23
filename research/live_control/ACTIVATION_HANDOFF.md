# Post-activation sampled handoff candidate

The ready-replan episode saved X104 but its full edit program expired. The
first-click pixel contract supplied a one-second capture-based deadline to all
steps, including text entry and Save. Separating those lifetimes requires an
explicit handoff; merely extending the old target deadline is insufficient.

activation_handoff_v1.py is a pure checker intended for validated durable
continuation records. It accepts only a matching, fully completed click/observe
program, verified empty input release, and a newer observation captured after
the terminal timestamp. It requires a matching fresh clock sequence, an age
below one second, unchanged surface/focus/geometry across capture samples,
empty owned input, zero sampled physical modifier/button mask, and a pointer
still at the activation point. It returns no deadline or input authority.

The proposed caller must explicitly create a distinct bounded keyboard-only
program after this check, retaining unique action IDs and pending-command
protection. Expiry, cancellation, partial completion, context change, or an
unresolved command must never cause automatic tail replay. This caller is not
implemented here; the helper is not yet a live default.

probe_activation_handoff_v1.py replays the actual first selection activation
and first later passive sample from ready-replan-ink-01. That record passes.
Fourteen mutated-record controls refuse interrupted statuses, wrong action,
partial steps, failed release, pre-release capture, stale age, sequence mismatch,
changed binding/focus, held input, and moved pointer. Results and source hashes
are in results/activation-handoff-controls-01. This is archived evidence plus
synthetic refusal coverage, not a new real execution or a latency improvement.

Limits: same-window widget focus can change without changing these fields.
Samples do not establish semantic identity, UI readiness, or atomic safety
between check and input. The helper expects validated records and is not an
untrusted wire-format parser. No task completion is inferred. Next integrate
the explicit two-phase caller against socket_v8/executor_v9, capture the extra
round trips and deadlines, and independently score the saved artifact while
requiring both program terminals to complete.
