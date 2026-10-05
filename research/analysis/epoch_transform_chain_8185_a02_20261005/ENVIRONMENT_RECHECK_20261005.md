# Post-STOP environment recheck

At 2026-10-05 12:45:15 UTC, a later read-only check ran `docker --context orbstack image ls --no-trunc` once. It again failed with `operation not supported`, this time while opening content blob `sha256:9c412ba8f50d0199ed2322a947b72c5a7416e0840c1bc8290335ecd31e25b07d` under OrbStack's containerd content store.

At 2026-10-05 12:48:52 UTC, the same read-only command returned the same blob error. Exact output and both observation times are in `ORBSTACK_RECHECK_20261005.txt`.

After the goal resumed, at 2026-10-05 12:53:00 UTC, the read-only inventory failed again on blob `sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa639`. The daemon still answered `docker info` as version 29.4.0. This is a runtime readiness check, not an allocation or scientific invocation; exact output is appended to `ORBSTACK_RECHECK_20261005.txt`.

These are post-STOP runtime-state observations only. They do not change the original A02 allocation receipt, whose candidate/auditor/construction counts remain zero, and are not retries of any scientific invocation. No image pull, store repair, alternate runtime, or host candidate execution occurred. Further image-list retries are stopped.
