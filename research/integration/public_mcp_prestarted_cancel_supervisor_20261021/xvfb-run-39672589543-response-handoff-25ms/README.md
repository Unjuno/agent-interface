# Standard-caller blocked-I/O Xvfb result — run 39672589543

**Disposition: scoped response-deadline PASS with independent release readback; runtime cleanup remains UNKNOWN.** This is a fresh private-Xvfb result from the PR #9331 workflow after the caller-response handoff margin was added. It is a separate run from the 301.268 ms response in run 39669924300; it does not overwrite that first outcome or establish a latency distribution.

## Frozen source and conditions

- GitHub Actions [run 39672589543](https://github.com/Unjuno/agent-interface/actions/runs/39672589543), workflow `Runtime X11 v1 Integration`, job `x11-integration`.
- PR head `6018b66032509c9747469cc70195b4d796ab1d7a`; workflow merge SHA `0db260cdb7fc9a6f3e7e2ef4b21a37948e7bb24b`; base main `59fe306fed57e54fe332e1d190c7628c1e89bb0d`.
- Ubuntu runner, CPython 3.12.15; Xvfb `2:21.1.22-1ubuntu1.3`, binary SHA-256 `97623d8c3972051fa29db5a91f64439b418a1ebc63ce449193556fc33900048e`.
- The owner was blocked in `python-xlib Display.sync()`. The prestarted supervisor was disabled. The child cancellation acknowledgement was withheld for 1 second; the delayed-request horizon was 8 seconds. The cancellation receipt carried a 300 ms caller-response deadline and 3 s transaction deadline.
- The raw JSON and observation PNG were downloaded from the named Actions artifact unchanged. Their hashes are repeated in `conditions.json` and this packet's `SHA256SUMS`.

## Outcome

The public MCP cancel response returned in **276.446613 ms**, 23.553 ms inside the 300 ms response deadline. The event-loop heartbeat ran 231 samples at a 1 ms period with a 2.549 ms maximum gap. The owner process retired with exit `-15`; the XRes disconnect observer reported the retired owner disconnected after 53.013 ms.

A fresh release worker then reported a verified all-keys-up state and exited cleanly after 386.005 ms. A separate parent X client read both `a` and `b` as up. At 8,501.037 ms after cancellation began, the independent client still read both keys up and observed no delayed `b`. The independent synthetic task oracle passed its exact initial/final effect, release-readback, and delayed-horizon checks.

The runtime cancellation result nevertheless remained `cancel_unconfirmed`, `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, `replay_allowed=false`, and `late_server_request_possible=true`, because the owner acknowledgement was not confirmed before retirement. The external synthetic oracle does not override that conservative runtime receipt.

## Limits

This is one non-prestarted private-Xvfb result. It demonstrates a caller response within the recorded deadline in this schedule and an independent global key-state readback; it does not establish causal improvement over run 39669924300, reliability, owner-exclusive input release, removal of already queued requests, fresh-target recovery, product task success, physical desktop transfer, WSLc portability, or matched efficiency. No WSLc allocation was used. The repeated observation PNG is byte-identical to the prior run's image; the JSON is new and records this run's distinct outcome.