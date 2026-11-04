# Current-main delayed release and fresh-generation recovery regressions

## Conditions

The tests ran in Docker Engine 29.8.1 after applying the host profile recorded in `.wslconfig`: 32 GiB RAM, 12 CPUs, 16 GiB swap, and gradual memory reclamation. The exact engine resources were 12 CPUs and 33,658,007,552 bytes. The cached image was pinned by image ID. The container had no network, read-only source, 2 CPUs, 4 GiB memory with 4 GiB total memory+swap, 256 PIDs, and init enabled. The host tree matched `origin/main` at the recorded SHA at execution time.

## Results

Three public owned-process supervisor regressions passed in normal and optimized Python (3/3 each):

1. A deliberately delayed cancellation release completed after the former 3 s budget. The Fake X state became neutral and the owner release attempt was `readback_verified`; the overall cancellation receipt correctly remained `release_confirmed=false`, `task_success=null`, and replay denied.
2. A blocked cleanup worker reached its finite deadline, was retired, and remained UNKNOWN. Fake X still showed the input down and no release/effect, so the test does not claim successful release after a timeout.
3. A fresh standard session/generation completed an independent synthetic task effect while the old cancellation receipt stayed UNKNOWN with `late_server_request_possible=true`; no old receipt was rewritten or replayed.

Docker exited 0, the engine remained responsive, and no container remained after `--rm` cleanup. This is one bounded post-configuration run, not a crash-rate estimate or proof that the settings fixed prior crashes.

## Scope

Fake X and synthetic application receipts only. No real application, provider/model request, live user input, WSLc allocation, or MAP01 run occurred. In particular, the first case's lower-level readback does not promote the caller's full `release_confirmed` field, and the third case's task receipt does not establish a real application result or efficiency.

Exact commands, raw logs, exit status, environment, and SHA-256 values are retained alongside this report.
