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

Key actions declare their logical controls.  The execution receipt must report a balanced
transition stream for each exact action/control pair; unrelated controls cannot satisfy
that coverage.  This binds the backend record to the requested keys but does not prove
physical key state or delivery to the target application.

Once execution has begun, stopping before a receipt arrives retains possible
occurrence, without claiming verified effect. Recorded cleanup does not undo
that uncertainty. Stops before an accepted begin and explicit no-effect receipts
remain no-effect. Release metadata is not physical input-release proof.

Effect evidence observed before its execution receipt's recorded start is
refused without changing lifecycle state. Equal-start observations, observations
during execution, and late receipt delivery remain representable. This assumes
comparable clocks and does not prove a final-action postcondition or clock truth.

An execution receipt refuses a release observation from before its execution start.
These timestamps must use a comparable clock. Equal timestamps remain representable;
the lower bound does not prove release after the final action or physical input state.
See the [retained regression evidence](../results/kernel-release-epoch-01a0ff34/README.md).

Lifecycle transitions require instances of their declared record classes before reading
record fields. Matching attribute shapes cannot bypass constructor validation at bind,
authorize, begin, execution/effect receipt admission or active cancellation. A refused
record leaves lifecycle state unchanged; the prior timestamp and release guards remain.
This nominal boundary follows the existing observation check and assumes trusted record
instances. It does not defend against hostile subclasses or mutation of public fields.
See the [nominal admission evidence](../results/kernel-nominal-records-01a0ff2d/README.md).

Run the complete kernel contract regressions with:

```text
python -B -m unittest discover -s runtime/kernel -p 'test_*.py' -v
```

This is an additive product contract, not a stable ABI.  Native backend adapters and
cross-platform acceptance are later promotion gates.
