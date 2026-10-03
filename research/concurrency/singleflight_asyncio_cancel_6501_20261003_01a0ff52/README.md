# Actual asyncio singleflight cancellation transfer boundary — #6501

**PASS_ASYNCIO_BOUNDARY_SCOPED**: 48 conditions / 120 caller outcomes in an actual
CPython 3.12.15 asyncio event loop, with one candidate and one separate raw-only
auditor invocation, both exit 0, retries zero. All eight effective corruptions
were rejected. See [the prospective plan](PLAN.md), [source/image freeze](FREEZE.json),
[raw events](execution/raw.json), [audit](execution/audit.json) and
[summary counts](SUMMARY.json).
No legacy #6501 allocation is invoked or changed. No runtime adoption or user-task
benefit is established by this research harness.

| Policy (12 conditions each) | Producer starts | Unaffected deliveries in one-cancel controls | Pending producers after all-cancel, before harness cleanup | Pending after cleanup |
|---|---:|---:|---:|---:|
| Independent | 30 | 6/6 | 0 | 0 |
| Direct shared await | 12 | 0/6 | 0 | 0 |
| Standard shield | 12 | 6/6 | 2 (one in each caller-count condition) | 0 |
| Shield + last-detach ownership | 12 | 6/6 | 0 | 0 |

The direct arm's six lost unaffected deliveries are the negative comparison,
not exclusions or unsafe actuation observations. Every arm refuses all five
generation-change caller outcomes as STALE and reports all five owner failures.
Plain shield needs an explicit producer owner to terminate work after all callers
leave; the small reference counter is one serialized-event-loop illustration.
Final cleanup was observed for all tasks in all 48 conditions. None of these
counts measures useful GUI effects, elapsed-time advantage or real offered demand.

The raw file is 136,089 bytes; SHA256
`d3262358814f4fd724d0b36b0fc027d2b4fee70f5a7e56a090d8ee794c5c2441`.
Source commit `88126633f0616f12d6510cab114e11267a7644f4` preceded invocation;
[candidate receipt](execution/candidate-receipt.json) and
[audit receipt](execution/audit-receipt.json) retain actual UTC start/end and exit.
Both [candidate environment](execution/candidate-environment.json) and
[audit environment](execution/audit-environment.json) match all five frozen hashes,
`cpu.max=25000 100000` and `memory.max=134217728`. The dedicated OrbStack guest's
Docker daemon was used; no shared host daemon repair/restart occurred. Original
source/raw bytes were copied back and read against their hashes. The own guest is
stopped and retained for reversible recovery; no other guest/container was changed.

Construction: five mini-tests passed on native macOS CPython 3.14.5 and the frozen
Linux image before allocation. Those transcripts were observed in tool execution;
they were not separately saved or rerun to manufacture log files. Shared Docker's
initial inventory failure is an infrastructure observation, not a candidate failure;
no candidate was submitted to that daemon. Guest setup/build and interpreter probe
were separate from the formal candidate/auditor.

Adopt the cancellation-separation/owned-cleanup requirement as a transfer condition
for a future actual read-only coalescer; this package does not integrate a broker.
Dynamic joins, TaskGroups, noncooperative reads, ABA, semantic equivalence, live
task effects and efficiency remain untested. Raw-only audit is a separate
implementation authored by this worker, not non-author review. Two non-author
FINAL-v5 content votes, current-base combination and conditional main application
remain separate from this result. Optional hosted CI is not claimed passed.

The strongest simple comparator is standard Python `asyncio.shield`. The extra
remaining-waiter counter addresses only its all-waiters-gone work-ownership residual.
No learned controller, mandatory local model or new authority is introduced.

Scripts are explicitly invoked; no repository runtime import, workflow, packaging
or automatic test discovery entry is changed. Construction checks use small
fixtures and remain separate from the one-shot 48-condition candidate.

Reproduce only as a new construction run or separately prospectively identified
allocation, preserving the retained first result. Inside an isolated Linux Docker
guest, copy the frozen source into `/root/6501-source`, keep `/root/6501-a01` new,
then invoke the following with the exact image digest from FREEZE.json:

```sh
docker run --rm --pull never --network none --read-only --cpus .25 --memory 128m \
  -e PYTHONDONTWRITEBYTECODE=1 -v /root/6501-source:/src:ro \
  -v /root/6501-a01:/out -w /src IMAGE python /src/run_record.py candidate --out /out
# Only if candidate exit is 0; distinct invocation/process:
docker run --rm --pull never --network none --read-only --cpus .25 --memory 128m \
  -e PYTHONDONTWRITEBYTECODE=1 -v /root/6501-source:/src:ro \
  -v /root/6501-a01:/out -w /src IMAGE python /src/run_record.py audit --out /out
```

`IMAGE` is a placeholder, not an invented mutable image freeze. The actual commands
and observed guest/cgroup/source/image identities are retained with executed results.
Formal retries are forbidden; retained-raw auditing can use separately named outputs.
