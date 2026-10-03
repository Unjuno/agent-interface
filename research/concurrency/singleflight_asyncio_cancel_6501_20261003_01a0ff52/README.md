# Actual asyncio singleflight cancellation transfer boundary — #6501

Prospective source package; executed first outcomes will be added after the freeze.
See [the prospective plan](PLAN.md) and [source/image freeze](FREEZE.json).
No legacy #6501 allocation is invoked or changed. No runtime adoption or user-task
benefit is established by this research harness.

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
