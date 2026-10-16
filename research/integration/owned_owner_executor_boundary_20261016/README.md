# Actual Executor composition: missing remote cancellation relay

2026-10-16, parent [#59](https://github.com/Unjuno/agent-interface/issues/59).
**Decision: reject direct RPC-owner substitution.** The independent service is
qualified only at its documented library boundary; normal completion and final
release do not establish cancellation delivery during a stalled parent worker.
No production adapter or default backend selection is added by this packet.

## Fixed construction and first results

The [test](../../live_control/test_owned_owner_executor_boundary.py) uses the actual
`doom_process_identity_backend_v1.Backend` and `executor_v13.Executor`, actual
selected source admission, strict transition/native owner, current RPC v2 and
owned service v3. Display, capture, focus/generation queries and input are Fake X.
Remote cells add only `client.owner_id=accepted_startup.owner_id` to reach the
actual backend protocol; this deliberately incomplete metadata shim is not an
adopted adapter. Local empty construction owners are closed before substitution.

Windows/Python3.13.14, same dependencies as the [owned-process packet](../owned_owner_process_v3_20261016/README.md).
No WSL/container/game/model/provider/real display or input. Ordinary construction
tests, no formal allocation consumed or replayed. Run:

```
python research/live_control/test_owned_owner_executor_boundary.py OUTPUT.json
python -O research/live_control/test_owned_owner_executor_boundary.py OTHER.json
```

Each mode runs three predetermined cells on the same source. `first-normal.*`
and `first-optimized.*` retain original outputs: three methods passed, zero
failures/errors/skips, three rows and49 loaded source pins per mode. Accepted
service startup additionally records child mode0/1 and source hashes. Original
Fake edge bytes, checksums, observation/intent/target binding, events, terminal,
parent cancellation/cause and exact owned-process final result are retained.

| Cell | Worker pause / cancel observation | Final cleanup |
|---|---|---|
| local selected owner | Pause after real backend down returns. Executor cancel sets parent lease; local owner releases while worker remains paused, with a parent interruption cause. | Cancelled, release verified. |
| remote metadata shim | Same pause/cancel. During a fixed250ms observation window, child trace contains only press, parent cancel is set, parent cause is absent and no input_released event exists. | Resume lets the worker send the cancelled lease with its next RPC; child then releases. Cancelled terminal, joined service exit0/verified. |
| remote metadata shim normal | No injected pause/cancel. | Actual Executor completes, release verified; joined service exit0/verified. |

This window is diagnostic, not a physical release-time requirement or universal
latency estimate. Saved timestamps establish press before cancel, observation
before release and observation before the original ten-second lease deadline.
The worker is paused after successful down, not inside a blocked native call;
this isolates propagation of a *later* parent cancellation between RPCs. It does
not measure cancellation delivered over a future independent transport, real
blocked X11 behavior, GUI timing or task success. Parent and child monotonic
timestamps are compared on this single host. No result is transferred to WSLc.

`read_saved.py` imports no runtime/process/input implementation. It validates
the exact three-cell inventory, original bytes/hashes, loaded sources, target
generation/deadline, pause/cancel/edge timing, distinct control outcomes, startup
and recovery/finish joins, and owned child exit. It rejects nine altered records
per mode; see `readback.json`. Four recorded owned child PIDs were absent at the
read-only check in `pid-absence.json`; this is a timed observation, not PID-reuse
proof. `review.txt` records the bounded immutable-code review. SHA256SUMS.txt
covers all packet members except itself.

## Required next implementation

RPC v2 serializes cancellation at request send; decoded child Lease events are
separate objects. A parent cancel between requests cannot update the child.
Adding owner_id or accepting a successful terminal does not repair that gap.
Under#59, implement a cancellation path independently serviced from the ordinary
request/reply worker, bound to service generation and original intent/source.
Preserve cancel-before-registration ordering, bounded inventories and unknown
delivery; relay the matching owner release cause back to the original parent
lease without granting replacement authority. Verify it while the actual parent
worker remains paused and while an ordinary RPC is in flight; retain failed
release custody and initial unverified results. Then wire explicit service
selection through the backend/Executor rather than shipping this test shim.
Controller/session death and native/task/economics qualification remain later
gates. This continues existing work without another coordination Issue.
