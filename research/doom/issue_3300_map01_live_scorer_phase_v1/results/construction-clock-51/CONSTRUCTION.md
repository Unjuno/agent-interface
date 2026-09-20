# Construction-clock-51 — userspace PMU counter preflight

## H/T/D/C/U

- **H:** The OrbStack linux/arm64 guest exposes a userspace PMCCNTR_EL0 with effective resolution near or finer than 1 ns, potentially improving run48's 24 MHz CNTVCT phase clock.
- **T:** In a read-only, network-none run48 image, compile a tiny C preflight and read CNTVCT/CNTFRQ and PMCCNTR around five 100 ms monotonic waits. Catch SIGILL rather than retrying or elevating privileges. No ViZDoom game, WAD, or formal path is started/mounted. STOP if PMCCNTR traps, stays constant, or effective frequency is below 1 GHz.
- **D:** Preserve source, exact Docker invocation, stdout/stderr and an independent arithmetic/gate audit. Compute effective PMCCNTR rate from each counter delta divided by CLOCK_MONOTONIC delta; compare with CNTVCT rate. No value is inferred if access faults or counter does not advance.
- **C:** This checks only counter availability/resolution in the current VM. A usable PMU counter would not by itself bound getter-call windows, event-entry latency, instrumentation perturbation, or qualify the formal phase experiment.
- **U:** PMCCNTR access and effective frequency are unknown before preflight. Formal allocation remains 0/120.

## Stop rule

No capabilities, host tracing, writable root, or game session. If the no-game preflight fails, record that exact STOP and do not try alternate privileged routes in this experiment.

## Observed disposition

Attempt 1 compiled the C probe but the chosen `/tmp` `noexec` mount prevented executing it (`Permission denied`); the PMU read did not run. Attempt 2 enabled execution only on isolated tmpfs, but Docker returned `unexpected EOF` and the host Docker socket was briefly absent. A later no-op container succeeded and Docker Engine responded, but no PMU output was captured. We stopped without repeating the PMU access. Independent audit: `STOP_RUNTIME_DISCONNECTED_DURING_PREFLIGHT`; PMCCNTR capability remains unknown, not failed. No game or formal row was started.
