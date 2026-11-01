# Delayed XTEST request with matched stop and autorepeat settings

This fixed-order WSLc pair follows the [earlier delayed-request experiment](../wslc_queued_input_retirement_20261101/README.md), whose non-retired positive control did not share the server-stop or autorepeat conditions. In both new arms global X autorepeat was disabled and read back as off. An actual spawned guarded owner sent `a` to a separate target; a test hook then issued and flushed an XTEST `b` press with an 8,000 ms delay on the same connection. The harness observed `a` down, stopped the private Xvfb for approximately one second, then resumed it. One arm started cancellation while stopped and retired the owner; the other withheld cancellation and kept the owner alive through the observation horizon.

| Observation | Cancel and retire | Keep owner alive |
| --- | --- | --- |
| Xvfb stopped | approximately 1.000 s | approximately 1.000 s |
| Old target `b` presses through 9 s after flush marker | 0 | 1, approximately 8.001 s after marker |
| `b` key state at horizon | up | down; fixture then released it |
| Old operation / cleanup | `UNKNOWN`, release unconfirmed, no replay | owner was later retired; cleanup `UNKNOWN` |
| Fresh guarded task | separate target received `a`, release verified, final input neutral | same |

The retired arm's prestarted cleanup worker observed the old owner disconnect and its `a` release readback was verified; an independent keymap also showed `a` up. In the alive arm the harness released old `a` before the horizon and later released `b`; these are fixture actions, not a recovery receipt. Both old operations remain unconfirmed. The marker proves client-side issue and flush, not when the X server accepted the delayed request. The controlled positive arm shows the request can reach the target under the same stop and autorepeat settings, but cancellation and cleanup necessarily differ between arms. One fixed-order pair does not prove that arbitrary server queues were drained: the old target log and horizon keymap cannot rule out transient events elsewhere or beyond the horizon.

Both allocations used main `e5925b6bd99fd4ff3f8e0bda5ed4d7cc02d92c4d`; the modified owned-session, cancellation supervisor and private-display module match draft [#10088](https://github.com/Unjuno/agent-interface/pull/10088) `926ba07214b5ab53ff38f66af5c0947606850118`. Other source is the earlier [#10074](https://github.com/Unjuno/agent-interface/pull/10074) snapshot, retained as a mixed tree. The pinned image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25` ran with one CPU, 1 GiB memory limit, no network and no pull; WSLc reported swap was not limited.

Both launchers returned zero on the frozen fixture criteria. [raw.zip](raw.zip), SHA-256 `4517478664d623b7aa17d244cc273bf2ecbb402bac0476e2e55614c8b9fc3091`, retains source, conditions, logs, events and receipts; ephemeral authority files are excluded and the archive was checked for their key bytes. The audit checks hashes, stop and horizon timing, target events, key states, cleanup status and fresh task releases. This is not proof of natural-failure recovery, automatic display replacement, old-task success, production MCP integration, a hard deadline, MAP01 completion or general reliability.
