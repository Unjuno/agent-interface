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

An execution receipt refuses a release observation from before its execution start.
These timestamps must use a comparable clock. Equal timestamps remain representable;
the lower bound does not prove release after the final action or physical input state.
See the [retained regression evidence](../results/kernel-release-epoch-01a0ff34/README.md).

Run the kernel and release-boundary regressions with:

```text
python -m unittest runtime.kernel.test_kernel runtime.kernel.test_release_epoch -v
```

This is an additive product contract, not a stable ABI.  Native backend adapters and
cross-platform acceptance are later promotion gates.
