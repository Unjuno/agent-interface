# Runtime kernel v1

This package is the platform-neutral mechanical seam for promoted Agent Interface
semantics.  It contains no model calls and imports no OS-specific backend.

The kernel does not claim that Windows, macOS or generic Linux are already supported.
A backend earns support by implementing `PlatformBackend` and passing its own
correctness/release evidence.  Backend registration is explicit and lazy, so importing
`runtime.kernel` never imports X11, Win32 or macOS frameworks.

The v1 lifecycle is deliberately small:

`Observation -> TargetBinding -> AuthorityLease -> ExecutionRequest/Receipt -> EffectReceipt`

Every transition checks the observation sequence, surface, lease, command and invariant
manifest identities.  Terminal execution requires a verified empty release.  Effect
verification is separate from effect occurrence; a contradicted effect is never rewritten
as pre-effect/no-effect.

This is an additive product contract, not a stable ABI.  Native backend adapters and
cross-platform acceptance are later promotion gates.
