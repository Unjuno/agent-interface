# MAP01 early typed cancellation live v2

V2 is a new allocation repairing the retained v1 failure. Executor v11 preserves
the established v3 exception identities while adding the same immutable program
SHA-256 attestation. Controller v37 also writes the exact typed invalidation
receipt before requesting cancel or validating any terminal, so a later wrapper
failure cannot erase capture-to-decision evidence.

Fixture, seed, controller-authored held-fire action, visible-ammo validity rule,
one episode, zero retries and zero model calls remain fixed. Thresholds remain
60ms capture-to-guard-decision,75ms capture-to-cancel and125ms capture-to-terminal
release. Every typed/full event must reconcile by epoch, binding, RGB hash and
health/ammo. A matching attested acceptance, cancellation, `cancelled` terminal,
empty release, no later input and process exit zero are mandatory.

All22 frozen source hashes verified before execution. The allocation then ran
exactly once and failed without retry. The typed guard decision arrived36.248ms
after capture and the matching cancel request at60.373ms, both within their
60/75ms thresholds and substantially earlier than the retained full-artifact
128.488/136.780ms baseline. The terminal is correctly `cancelled`, the program
attestation and all three typed/full reconciliations pass, no later input was
admitted, and the runtime process exits zero.

The preregistered terminal release receipt arrived131.094ms after capture,
6.094ms beyond its125ms threshold, so the allocation remains failed. Raw owner
evidence independently verifies that the X11 keys/buttons were already empty at
63.484ms. That earlier record is descriptive and does not retroactively replace
the frozen terminal metric. Artifact publication occupied the intervening path,
and final cleanup emitted a second release only after it completed.

The23 pre-retention files and1,225,288 bytes are preserved under
`results/map01-early-typed-cancel-live-02`. Independent Windows/WSL audits verify
the manifest, frozen sources, sole failed check, event ordering, clean release,
reconciliations and zero model calls. The next candidate should publish an exact
identifier-bound owner-release state while program/artifact finalization remains
pending; terminal closure stays a separate later lifecycle event.
