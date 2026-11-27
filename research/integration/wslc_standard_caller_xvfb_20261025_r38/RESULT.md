# R38 — WSLc 3.6 s private-Xvfb pause under a 4 s transaction deadline

**Disposition: `PASS_SCOPED_4S_TRANSACTION_3600MS` (27/27 audit checks).** The unchanged public standard-caller test ran once in a digest-pinned Ubuntu container through Docker Desktop on the user-authorized PC. Networking was disabled; the container had 2 CPUs, 2 GiB memory, a 128 PID limit, an executable private 512 MiB `/tmp`, read-only repo/dependency/stage/XKB mounts, and a writable output mount. The exact container and Xvfb process were removed after the run.

Xvfb was paused for 3600.317 ms and resumed through its retained pidfd. The public cancel call returned in 315.665 ms. Supervisor release/readback completed 3734.767 ms after transaction admission, leaving 272.051 ms before the exact 4,000 ms deadline. Independent parent readback saw all keys up at +3884.460 ms. The +8504.474 ms horizon found all keys up and no delayed `b` press.

Old and fresh synthetic task oracles passed. The fresh effect count changed 0→1 and stayed 1 at the horizon; input invocation to independent effect readback completed in 46.608 ms. The old cancellation remained UNKNOWN and replay-denied. Runtime cancellation fields remain UNKNOWN, `release_confirmed=false`, `replay_allowed=false`, and `task_success=null`.

## Scope

This is one synthetic-Xvfb sample at a 3,600 ms pause, 100 ms longer than R37. Its 272.051 ms release margin is narrow and does not establish a general safety margin. It does not establish Windows desktop, MAP01, real-application transfer, broad reliability, or matched efficiency. See the preregistration, raw output and 27-check audit in this directory. The initial audit attempt is retained; it had a false negative because it expected Docker's absent-object error to say `no such object` instead of the observed `no such container`.
