# R37 — WSLc 3.5 s private-Xvfb pause under a 4 s transaction deadline

**Disposition: `PASS_SCOPED_4S_TRANSACTION_3500MS` (26/26 audit checks).** The unchanged public standard-caller test ran once in a digest-pinned Ubuntu container through this PC's Docker Desktop. The container had no network, 2 CPUs, 2 GiB memory, a 128 PID limit, a private executable 512 MiB `/tmp`, and read-only repo/dependency/stage/XKB mounts. The exact container was removed after the run.

Xvfb was paused for 3,500.413 ms and resumed through its retained pidfd. The public cancel call returned in 317.041 ms. Supervisor release/readback completed 3,622.695 ms after transaction admission, leaving 377.305 ms before the exact 4,000 ms deadline. Independent parent readback saw all keys up at +3,752.893 ms. The +8,504.193 ms horizon found every key up and no delayed `b` press.

The old synthetic task and the separate fresh-generation task both passed their independent exact-effect oracles. The fresh effect count changed 0→1 and remained 1 at the horizon; input-invocation to independent effect-readback completed in 49.969 ms in this synthetic Xvfb fixture. The old operation remained fenced as UNKNOWN after the fresh task.

Runtime cancellation still reports `cleanup_status=UNKNOWN`, `release_confirmed=false`, `replay_allowed=false`, and `task_success=null`. The independent task oracle does not upgrade these runtime fields.

## Scope

This is one containerized synthetic-Xvfb sample at a more severe pause than R30's 2,950 ms. It does not establish Windows desktop, MAP01, real-application transfer, broad reliability, or matched efficiency. R31–R36 are retained setup stops before the test body; none emitted input. Their diagnoses and the complete R37 raw/audit packet are preserved alongside this result.
