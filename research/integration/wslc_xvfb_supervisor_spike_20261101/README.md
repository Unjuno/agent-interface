# Private Xvfb supervisor spike: retained key versus display replacement

This is an experimental test harness, not an integrated recovery API. It creates and owns a private Xvfb, opens a pidfd to that exact process, sends a fixture `a` key press to an independent old target, verifies both the target effect and global key-down, and stops the server. Two fresh WSLc allocations, frozen before execution, then compare pidfd retirement and a new display with resuming the same display. A fresh spawned guarded owner subsequently types `a` into a separate target.

| Observation | Retire and replace | Resume same display |
| --- | --- | --- |
| Before stop | old target received `a`; key down | same |
| Intervention | pidfd SIGKILL; old Xvfb exit -9; new Xvfb on a different display | pidfd SIGCONT on old Xvfb |
| Fresh target key readback | `a` up | `a` still down |
| Before fresh task | already neutral | fixture explicitly releases old `a` |
| Fresh guarded task | target value `a`, press/release, guarded release verified, neutral input | same, after fixture release |

The resumed control's fresh target also recorded the fixture's `a` release **before** the new action's press/release. The old target exited with code 1 after its X server was killed; the fresh target exited 0. In the resumed control both targets exited 0. A neutral new server is not a verified physical release on the retired server, and killing a display destroys its application context. The harness must own an actually disposable display and all affected clients; this spike does not enforce that requirement in production.

The held key was sent by a fixture, not an old guarded input owner, and no delayed old server request, cancellation operation, reconnect using an old credential, or shared-display containment was tested. The follow-up action used draft [#10074](https://github.com/Unjuno/agent-interface/pull/10074) head `0675ab810f7ee890d0904b8a402678c81f8dbafb`; it does not establish integration with the cancellation path. This is one fixed-order pair on a single host, not a hard deadline, general recovery guarantee, MAP01 completion, or reliability estimate. Compare the earlier manual display replacement evidence in [#9814](https://github.com/Unjuno/agent-interface/pull/9814).

Both new allocations used pre-run main `84a79c42f216aad880e3aa779801f652a220c212`, pinned image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`, one CPU, 1 GiB memory limit, no network and no pull. WSLc reported that the memory limit did not include swap. Both launchers returned zero. [raw.zip](raw.zip) retains the source, conditions, logs and target receipts; SHA-256 `e631b009ab1eeb2c8530f9875d673ad24a7af9b3832e6fe502c7a7c0d24ac3ad`. The audit checks frozen hashes, intervention order, the contrasting key state, exact target event order, fresh action release, process exits and archived hashes.
