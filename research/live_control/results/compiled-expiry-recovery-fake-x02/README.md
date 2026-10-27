# Explicit recovery after uncertain release: Fake X x02

This fault injection composes the actual compiled core, guarded X11 adapter, NativeHandleBridge and X11RuntimeSession over repository Fake X. The lease expires after CTRL is pressed. The transaction attempts cleanup, but its first physical readback is deliberately made to report CTRL still down, so the runtime retains an input-recovery requirement and returns an incomplete failure with zero completed transitions. The test then invokes the explicit release-only recovery API using the current binding revision. A second release/readback succeeds; no program action is replayed, task success remains null, a new binding revision is issued, and window review remains required.

`raw.json` contains the input event sequence, compiled-core receipt, stored raw execution and terminal records, exact injected conditions, and explicit recovery receipt. Its SHA-256 is recorded below.

- SHA-256: `350f9f41fe0f2d912001de42b9557d92b1a4b0e9cbc85e82fe0fa10d8954ad97`
- Classification: offline Fake X fault injection only
- It does not test Docker, a live X server/application, task-effect correctness, or a hard bound on blocked native I/O.
