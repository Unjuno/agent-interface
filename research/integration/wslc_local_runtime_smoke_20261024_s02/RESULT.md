# WSLc local runtime smoke S02

**Disposition: `PASS_WSLc_READONLY_RUNTIME_SMOKE` for this one bounded probe.** This does not satisfy the computer-control, MAP01, task-effect, release, recovery, matched-efficiency, or broad-reliability gates.

The attached Windows PC was explicitly authorized for this task. Before the run, WSLc 3.0.3.0 reported zero running `wslc.exe` clients, and a scoped query for the newly generated container name returned exit 0 with no match. No global container inventory was used. The exact pinned Python image was initially absent; one bounded pull fetched digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` in 12.141 seconds. The run used that digest with `--pull never`, `--network none`, one CPU, a requested 512 MiB memory limit, a read-only bind, a 90-second run timeout, and `--rm`.

The container read the 19-byte sentinel exactly and rejected the write with `EROFS`. The runner retained a full 64-character CID and queried only that exact CID after exit; the query returned no match. The bounded run completed in 0.792 seconds with exit 0. Eight offline audit checks passed; their results and receipt hashes are in `audit.json`.

The runtime emitted `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Therefore the requested 512 MiB value is not evidence of a hard memory ceiling or swap isolation. The probe did not exercise computer input, release or recovery behavior, application task success, MAP01, efficiency, or reliability.

The first local wrapper invocation failed to import the helper module from a relative path before starting `wslc.exe`; it is preserved in `image-pull.json`. The corrected bounded invocation made one image pull, and the runtime probe itself was attempted once. S01's prior `HOLD/UNKNOWN` result remains unchanged.
