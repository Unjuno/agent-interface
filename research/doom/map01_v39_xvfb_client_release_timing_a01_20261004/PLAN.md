# MAP01 v39 Xvfb client release-timing construction A01

Issue: #59. This is a new, isolated construction experiment on the privately owned, network-isolated OrbStack guest used for the earlier A05 routing check. It does not reuse A05's candidate invocation or output directory. The current-main InputOwner v10 source is pinned independently.

## H/T/D/C/U freeze

**H.** With one local Xvfb server, both direct XTEST and InputOwner v10 should produce exactly one server KeyPress and KeyRelease for the focused test client. A dedicated receiver thread can timestamp event dispatch with the same guest `perf_counter_ns` clock used around calls. The X server event timestamps also give a millisecond-resolution interval between server-processed press and release. The owner-call receipt and client-event dispatch may occur in either order; both outcomes are recorded without a latency threshold.

**T.** Run one frozen candidate invocation with 30 paired cycles (direct XTEST then InputOwner v10 per cycle), one key and one focused client window. For each press, wait for the receiver thread to dispatch KeyPress before issuing that route's release. Record caller start/return, the owner admission acknowledgement where exposed, server event timestamp, receiver dispatch timestamp, and server keymap state before/after each edge. Use Xvfb on display :117 with TCP listening disabled, no game/model/GPU/physical input, and no network. A separate raw-only auditor checks the exact event pairs, keymap transitions, timestamps, owner cleanup, receiver shutdown, and Xvfb exit.

**D.** PASS only if all 30 cycles in both routes have one correctly targeted press/release pair, expected false→true→false keymap transitions, valid ordered timestamps, verified empty InputOwner close, stopped receiver thread, and Xvfb exit 0. Any completed mismatch is FAIL; missing dependencies, failed setup, or incomplete custody is STOP. No retries; preserve the first raw result.

**C.** This measures Xvfb/XTEST routing and client-thread dispatch, not application processing. X server event time has millisecond granularity; the client receipt timestamp also includes receiver scheduling. The direct route is a same-environment control, but fixed route order can retain order effects.

**U.** A guest cgroup check reported `cpu.max=max 100000` and `memory.max=max`, so effective CPU/memory caps are not established. The sample is tiny and the VM is isolated, but no cap-enforcement claim is made. No real GUI, game, model, physical key, useful task feedback, bounded recovery, or matched live-control benefit is established.

## Freeze identity

Source and candidate hashes are recorded in `FREEZE.json`. The machine is `v39-x11-routing-a05-20261004` (OrbStack machine ID `01M42N2F303RHWR42A763DRBNJ`, isolated and network-isolated). The candidate writes to a new A01 directory on the guest. A05 evidence remains unchanged.
