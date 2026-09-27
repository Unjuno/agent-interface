# Native result mapping successor (#2508)

This is a current-main additive successor to the stale #2512 branch. It exposes
a pure, fail-closed mapping only when explicit target surface/frame context is
present. Missing observation, missing acknowledgement, failed transport,
release errors, malformed revisions, and authority-promotion fields remain
uncertain or rejected.

No backend, GUI, input, model, network, authority, or task-effect call is made.
The mapping is contract evidence only; it does not prove that a native session
can emit the required context.