# MAP01 two-phase early release live v1

The retained v2 typed-cancellation run separated a real physical fact from its
late presentation: the X11 owner verified empty input at63.484ms, while the
terminal carried cleanup evidence only at131.094ms after exact artifact work.
This candidate makes those two phases explicit without weakening either one.

Executor v12 uses the existing lease-cause and InputOwner v10 mechanisms. Each
accepted program now has a fresh opaque intent token. A cancellation starts a
separate bounded watcher; only the owner can record the lease-bound release.
When that record proves empty keys/buttons, Executor emits `input_released` while
the worker and artifact may remain active. Running-action guard v3 then enters
`REVOKED_INPUT_RELEASED_AWAITING_TERMINAL`: current authority is false, physical
release is true, a new decision is required, and program terminal is still
pending. A later matching cancelled terminal remains mandatory.

Synthetic construction deliberately leaves finalization blocked for80ms and
shows the release event first. Wrong tokens, unverified release, pre-cancel time,
duplicate release and terminal time reversal fail closed. Controller v38 consumes
cancel, early release and terminal in that order. The focused suite passes37
existing/new tests plus the v38 integration on both Windows and WSL.

One live allocation is frozen with the same fixture, seed, held-fire action,
visible ammo invalidation, one episode, no retry and no model call. Bounds are
60ms to guard decision,75ms to cancel,90ms to physical release and200ms to
terminal closure. It additionally requires release before artifact and terminal,
exact SHA/token binding, a no-authority pending state, later lifecycle closure,
all typed/full reconciliations, no later input and process exit zero. The output
was absent and all32 source/fixture hashes verified before execution.

The allocation then ran exactly once and passed every frozen check:

- invalidating capture to typed guard decision:31.857ms;
- capture to matching cancel request:54.578ms;
- capture to independently verified empty physical release:57.660ms;
- owner verification to `input_released` publication:9.321ms;
- capture to later terminal closure:133.698ms;
- physical release led terminal closure by76.039ms.

The lease token matched acceptance and release. Physical release was published
before both the full artifact and terminal. The guard exposed the pending state
with no current authority, then the cancelled terminal closed it. Screen ammo
changed48→47, no input followed invalidation, all three typed/full artifacts
reconciled, and the child exited zero. The22 pre-retention files total1,251,326
bytes and are hash-manifested. Independent retained audits pass on Windows/WSL.

This establishes one concrete shared runtime behavior under real X11 held input:
an agent can learn that physical input stopped without waiting for image artifact
or program lifecycle completion. It does not establish gameplay improvement,
cross-domain portability, model-use benefit or general human-tempo control. The
next test should transfer the same release event to a pointer/desktop interruption
or integrate it into a bounded planner episode, rather than repeat this fixture.
