# 2-vCPU COW Needle LoRA

Issue #4769 is a successor experiment to the concurrent online-LoRA/System-1
HOLD in #4653. It changes exactly one factor: the Docker CPU quota for the
same 60-Hz, 512-row online rank-2 LoRA workload, from 1 to 2 vCPUs.

No live task input or action authority is present. See `PREREGISTRATION.md`
for decision gates and limits.

## Files

- `runner.py`: one seed/CPU cell producer, with absolute query schedule and
  copy-on-write version publication.
- `audit.py`: raw-only independent data/training replay and exact proposal
  verifier; it does not import the runner.
- `formal.py`: one-shot host orchestration, Docker command receipts, and
  fail-closed source/freeze preflight.
- `test_construction.py`: zero-fit construction guards.
- `FREEZE.json`: exact source, GitHub readback, issue, seed, image and
  collision snapshot; added immediately before formal execution.

## Reproduce

Run the construction tests separately in the pinned local Docker image with
each CPU quota (1 and 2), network disabled, source/root read-only, and unique
empty output mounts. They execute no optimizer steps.

After source/freeze readback is complete, invoke the host wrapper exactly once:

```powershell
py -3.11 .\formal.py --source . --out <unique-empty-output-directory>
```

The wrapper runs six one-cell trainer containers (three seeds × two quotas)
and one separate audit container. A consumed formal output directory is never
reused. No retry or tuning is permitted.
