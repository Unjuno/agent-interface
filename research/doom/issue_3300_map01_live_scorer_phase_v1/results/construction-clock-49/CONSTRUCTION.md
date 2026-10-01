# Construction-clock-49 — counter-instrumentation CPU-cost control

## H/T/D/C/U

- **H:** The run48 per-tic counter/clock/ring-buffer instrumentation adds measurable process CPU cost during a passive 35 Hz async MAP01 episode relative to the same pinned ViZDoom source without the instrumentation.
- **T:** Build a no-patch control image by reversing only the run48 source patch, require the exact upstream commit and zero linked `MRS CNTVCT_EL0` instructions, then alternate four fresh-session pairs in a preregistered I-C/C-I/I-C/C-I order. Each arm runs hidden `ASYNC_SPECTATOR`, no action calls, and six seconds of 10 ms passive API polling. Record monotonic wall time, process CPU time, API tic values, binary hash, setup/cleanup, and (instrumented arm only) entry trace. Stop a row on identity/opcode/setup failure.
- **D:** Retain both arm rows per pair, exact invocation/build logs and image IDs, raw trace, independent pair-shape/gate audit and SHA-256 manifest. Compare paired process-CPU-seconds / wall-seconds; do not infer uninstrumented engine rate from the stale API snapshot.
- **C:** The estimand is coarse CPU cost under this pinned OrbStack linux/arm64 fixture and identical Python polling, not per-tic latency, schedule phase, missed tics, or timing accuracy. Four pairs are construction evidence only.
- **U:** Whether the instrumentation causes measurable process CPU cost in this fixture, and the observed between-session variance, are unknown before execution. Formal phase allocation remains 0/120.

## Preregistered order and stop rules

Pair order: instrumented/control, control/instrumented, instrumented/control, control/instrumented. Each container starts one fresh episode with seed `349000 + pair`; both arms use the same pair seed. Six-second windows, 10 ms polling, exact WAD hash, 35 Hz target. No action/advance calls. Preserve failed rows; never replace a failed pair silently.

This is an intervention-cost experiment, not a solution to the formal phase gate. A PASS can support only the measured CPU-cost contrast; absence of a detectable CPU difference cannot establish absence of scheduling perturbation.

Pair00 instrumented completed before a serialization review found its convenience `engine_entry_hz` used CNTVCT ticks as nanoseconds. The raw record is preserved unchanged; the audit ignores that field and derives an approximate VIZtime delta per measured wall interval from retained VIZtime range. Subsequent rows store the corrected rate label. The CPU-cost endpoint and row identity are unaffected.

## Observed result

The control image was rebuilt by reversing only the run48 patch from image `sha256:fdf45a138d5b025499f6808ae0b8a04a12d2ad4643e6618f913a85e1cfe64e17`, confirming the pinned source commit and clean source status, and requiring zero linked `MRS CNTVCT_EL0` opcodes. The control image ID is `sha256:05e01176ffcc2258ca88d7f8aafb6bd9e3915cd7ad19af196924008ff16f84b6`. The instrumented image had exactly one expected opcode. All eight fresh sessions initialized, completed the six-second window, and closed. Passive getters ran 465–495 times per session. The four instrumented traces retained 214–215 VIZ_Tic records, corresponding to approximate observed VIZtime rates of 35.48–35.65/s from wall-window delta; no control engine trace exists.

Paired process-CPU/wall ratios (control → instrumented for each pair) were: pair0 0.006614 → 0.008181; pair1 0.010534 → 0.009878; pair2 0.011493 → 0.011928; pair3 0.012047 → 0.010786. Differences were +0.001567, −0.000655, +0.000435, −0.001261; median −0.000110, with two positive and two negative. Independent audit: `PASS_CONSTRUCTION_ONLY_CPU_COST_COMPARISON`, 8 rows, zero errors. No consistent additional CPU cost was detected in this small paired sample.

In pair2, the uninstrumented control's public API tic values included 2, while the instrumented arm and the other controls remained at 1. This demonstrates snapshot progression is not invariant across these fresh passive sessions. Because the control engine's internal tic rate was not observed, the result neither establishes equal engine progression nor bounds scheduling perturbation. The exact-scorer phase question remains unanswered and formal allocation remains 0/120.

Build attempts 1–3 stopped on disassembly-command quoting. The first instrumented launch used the base image's default run48 entrypoint and stopped before game setup. One shell sequence attempt stopped before launching a container. These STOP logs are retained and excluded from the eight audited rows. A `Failed to create secure directory (/root/.config/pulse)` warning appeared in some successful headless rows; game setup/measurement/cleanup completed and the warning is not treated as scientific failure.
