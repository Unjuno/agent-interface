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
is absent and all32 source/fixture hashes verify. Run once and retain its first
result unchanged.
