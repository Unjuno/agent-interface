# Standard-caller Xvfb cancellation trace — r01

This packet preserves two distinct GitHub Actions observations from the private `Runtime X11 v1 Integration` workflow. It is one passing trace and one unexplained adverse run, not a replicated release guarantee. Both artifacts were copied byte-for-byte; verify them with `SHA256SUMS`.

## Conditions and provenance

- Repository: `Unjuno/agent-interface`; workflow runs [39252995939](https://github.com/Unjuno/agent-interface/actions/runs/39252995939) and [39256375123](https://github.com/Unjuno/agent-interface/actions/runs/39256375123), job `x11-integration`.
- The adverse run used source head `07d9b86...` (synthetic merge `3907b8ee65ce27d499454558432fe11ffa9032cc`). The traced run used PR #9189 head `0cec564fd34d10d31353e803167314b5d18d0a97`, merged as `ac5374f68ff8ea0e08ca8d75d1b0bdd3c9a4a782`.
- Both used isolated Xvfb, package `2:21.1.12-1ubuntu1.8`, binary SHA-256 `6b27845931670c8c9b3ce7423696a452ce3cab1c7f316ce5f7ea7f1297fa2f84`, synthetic app state, and one test trial per run. These are private hosted Xvfb observations, not WSLc, native desktop, or product-app trials.
- Run 392563 records the caller/owner process identity and retirement trace added by #9189. The owner was a child process of the caller; it was alive at cancellation entry and exited by SIGTERM (`-15`).

## Preserved outcomes

- **39252995939 — adverse, unexplained:** cancel returned in 4.906 ms while `owner_process_retired=false`, exit code was null, release was not attempted, cleanup was `UNKNOWN`, key `a` remained an obligation, and a late server request remained possible. Later close failed with `owned guarded session unavailable: failed`; teardown eventually released the key. Do not reinterpret this as a pass or silently discard it.
- **39256375123 — scoped trace pass:** cancel returned in 356.415 ms; the owner retired in 3.893 ms after cancellation entry; XRes observed disconnect; an independent release worker read back keys/buttons up in 308.617 ms; a separate parent observed `a=false`, `b=false`, and no late `b` press at 8.5 s. The standard caller still returned `release_confirmed=false`, `cleanup_status=UNKNOWN`, `late_server_request_possible=true`, `task_success=null`, and replay disabled.

The second run does not explain the first. Its independent readbacks do not promote the caller's release state, demonstrate a deadline under permanently blocked server I/O, establish task effect/success, or qualify bounded recovery. Keep Issue #17 open and release/task conclusions `UNKNOWN`. Do not rerun either consumed run; choose a future discriminator only with its own authorized, unconsumed allocation and evidence plan.

## Files

- `run-39252995939/`: raw JSON and observed PNG for the adverse run.
- `run-39256375123/`: raw JSON and observed PNG for the traced run.
- `SHA256SUMS`: hashes for all four retained raw artifacts.
