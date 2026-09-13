# Pointer caller: OpenTTD and Mindustry integration readiness

The unchanged pointer_socket_entry_v1 / pointer_exchange_v1 path now runs the
existing v9-backed OpenTTD and Mindustry entry points. Both domains reject an
already-expired request, cancel an active Shift hold with verified release, then
complete a known task replay and its independent score. This extends adapter
readiness beyond the earlier Inkscape episode; **it is not a same-model speed
comparison or new assistant gameplay achievement**.

| Domain | Task replay | Exact frames | Full retained records | Independent result |
|---|---|---:|---:|---|
| OpenTTD | Two known road-toolbar/drag programs | 8 | 54 | Three connected owned road tiles; 42-tile guard passes |
| Mindustry | Three known selection/drag/resume/pause programs | 14 | 80 | Six oriented conveyors; 112-tile guard; 48 copper delivered after control |

Each frame count includes the cancelled-hold observation. Both applications and
their owned fixture processes report cleanup, unchanged canonical save and bridge
exit zero. The source manifests, requests/replies, raw runtime records, snapshots,
images and task artifacts are archived. The audit compares every received prefix
with the entire raw event log and reconstructs all 22 AIT frames against PNG bytes.
It independently reruns the guarded road and split-baseline flow scores.

## Failed setup retained

The first OpenTTD attempt in `pointer-domains-01` exited with argparse status 2:
its existing adapter requires `--controller`, which the probe omitted. The stream
closed without any runtime events or task inputs. That attempt remains archived.
`probe_pointer_domains_v2.py` adds `--controller scripted` for OpenTTD and selects
one domain, allowing the failed domain alone to be retried in `pointer-domains-02`.
The wrapper/caller/backend source bytes did not change, and the successful
Mindustry episode was not rerun or silently replaced.

The Mindustry entry point's inherited manifest describes its original assistant
self-use purpose. **These new executions are scripted.** The enclosing plan and
result identify fixed-coordinate replay; treat those as the execution provenance,
not the inherited prose. There is no newly observed model reasoning in this study.

## What the stress checks prove

- An already-expired submission produces the legacy unattributed rejection before
  admission or input. It does not prove expiration during a blocked operation.
- The probe admits a four-second Shift hold and waits for its first observation
  after input admission. It sends cancellation on the separate cancellation
  endpoint and receives a matched cancellation, cancelled terminal and verified
  no-held-input state. This is an actual live cancellation, not a mocked reply.
- The subsequent task programs run through the new clock+submit caller and pass
  their oracles. Scripted coordinates are copied from known successful portions
  of earlier episodes. Mindustry waits three seconds before pausing for review,
  then uses its separate 600-tick delivery phase after input closure.

The recorded prior observation is not treated as freshly captured by a clock
query. Caller replies retain the records of rejected/cancelled operations. No
task input is automatically replayed after transport uncertainty. Probe cleanup
can send an explicit finish if a run fails; that is cleanup, not a task retry.

## Reproduce and remaining work

The v1 script preserves the missing-argument failure. Use v2 for a fresh per-domain
run with the existing asset prefix and a new output directory:

```sh
python3 research/live_control/probe_pointer_domains_v2.py --domain openttd \
  --root /home/taka/agent-interface-bench-feasibility --out /home/taka/pointer-openttd-rerun
python3 research/live_control/probe_pointer_domains_v2.py --domain mindustry \
  --root /home/taka/agent-interface-bench-feasibility --out /home/taka/pointer-mindustry-rerun
python3 research/live_control/audit_pointer_domains_v1.py
```

The audit targets the committed cohorts; [summary](results/pointer-domains-audit-01.json)
records their results. Plans hash new probe/caller/transport sources and historical
replay inputs before running. Each domain retains its existing runtime manifest.
This is not a complete OS/library lockfile. Software rendering and known ancillary
Java/audio limitations remain.

Pending: combined result/image display in actual-use calls, live stale-observation
and concurrent-client interference controls, mid-operation expiry/backpressure,
and corresponding live stress on Inkscape through this wrapper. Then pin the
whole candidate and counterbalanced actual-use allocation. Do not pool these
scripted replays with the earlier assistant episodes or compare their wall times
as a speedup: recovery errors and model decision boundaries were deliberately
absent here. No token savings, human-tempo result or Research Freeze qualification.
