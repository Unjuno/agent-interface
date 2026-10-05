# Native X11 construction decision gates

This ordinary construction uses exact PR #8094 head `2b0cb591c3ebcb84d1db983612613850c08fffea`; it does not claim fresh-main gameplay qualification. The source inventory contains 81 immutable Git blobs, of which import preflight loaded 32 modules for the measured backend. The driver and independent auditor will be hashed before the first candidate execution.

Use a fresh private Xvfb server and a small focused test window on the owned Debian bookworm machine. Use actual measured-backend construction, real Python-Xlib/XTEST and real server keymap state. Game/HUD/controller/planner behavior is outside the test. Do not patch input or measurement implementation methods. A driver that sets up the backend's program/step context must retain that fact; direct backend calls do not constitute a V39/Session invocation.

## Finite cases and pass criteria

1. **Ordered multi-key UP.** Admit three distinct supported keys with a finite lease. Retain the admission records and server keymap after the DOWNs. Request their UPs in reverse order through the actual release-batch backend. Require three distinct actuation identities, source-key/owner/intent identity matching between admission and UP, confirmed native-server keymap transitions, reverse release order in actual test-window events, complete release receipts and a neutral final keymap. Shared batch sample intervals must be ordered and bound the releases; they are brackets, not exact physical-event times.
2. **Cleanup-first cancellation.** Admit two keys under a distinct finite lease. Set the lease's real cancel event, await the owner's actual verified cancellation cleanup with a bounded deadline, then submit the deferred same-lease UP batch. Require exactly the original admitted identities in cleanup measurements, confirmed UP with `per_key_cleanup_snapshot`, cancelled cause preserved, no new key event or input actuation from the late batch, and verified neutral final server/owner state. No ordinary-release pair may be manufactured by this interruption path.

Each case must retain source hashes, raw owner/backend receipts, server keymap observations, initial admissions, native test-window event ordering, exception disposition and owner shutdown state. Stop on setup failure or failed precondition rather than calling it a scientific pass. Separate ordinary harness repairs, if needed, receive a new output directory and retained failure record; no formal allocation is being consumed or replayed.

## Independent audit

The auditor must reconstruct identity, key order, state transitions and cleanup disposition from raw; do not trust the driver's summary or a green exit alone. It must bind loaded source bytes to the frozen inventory. Missing or duplicate observations, mismatched identity, unverified final state and wrong late-batch cause fail. An observer event is evidence of delivery to this test client only. It is not independently useful game feedback or task completion.

## Environment and termination

One systemd unit runs as non-root `study`, private network namespace, private temporary directory, read-only source, 1 CPU quota, 1 GiB memory, zero swap allowance, 64 tasks and a finite wall limit. The earlier environment probe read back `cpu.max=100000 100000`, `memory.max=1073741824`, `memory.swap.max=0`, `pids.max=64`. Record the actual candidate's constraints too; configuration alone is insufficient evidence. No external model, network, GPU, existing display or foreign VM may participate. Outputs must remain below 250 MiB. Stop the owned Xvfb and VM after readback; retain every run and provisioning failure.

PASS remains **native virtual-X11 construction only**. It does not establish physical keyboard state, full V39 controller composition, live threat exposure, useful game feedback, recovery effectiveness, error rates, latency savings, or MAP01 completion. #59's live lane and main-merge quorum remain separate.
