# Preregistration — TASK-MEMORY-RETRIEVAL-7166-T0-HOST-A05-20261004

## Lineage / intake

A05 follows A04's STOP_STALE_MAIN_BEFORE_CANDIDATE (#7166 comment #5976355144).
A03's FAIL_METHOD (#5976328577) and A04's frozen STOP remain unchanged. Fresh
base main: `a2f6b60ac84300d45beb82c7cf5a6e06cfc7c456`. Issue #7166 is open.
This is a fresh allocation, not a replay or repair of A03/A04.

## H/T/D/C/U

- **H:** current-only => NONE; exact source-bound linear history => EVENT_CHAIN;
  identity/provenance/lineage ambiguity => ABSTAIN; no action authority. Six
  effective corruptions are rejected.
- **T:** deterministic 72-case fixture (six strata × 12), separate scorer-only
  oracle, candidate sees fixture only; one candidate then one independent
  raw-only auditor; mutation byte-difference is checked for all six controls.
- **D:** PASS_METHOD_SCOPED only for exact 72/72 reconstruction, zero authority,
  effective mutations 6/6, rejected mutations 6/6. Any mismatch/no-op is FAIL;
  base movement before invocation is STOP. Retries=0.
- **C:** finite authored fixture; it tests labels/provenance/abstention and
  auditor mutation sensitivity only.
- **U:** natural retrieval utility, model behavior, actual model-visible cost,
  task effect, GUI, latency, runtime and product benefit.

## Runtime / commands

Host-only macOS arm64, CPython 3.14.5, standard library. OrbStack content-store
failure is preserved at #7383 comment #5976132398 and will not be retried. No
container enforcement, model, GUI, network, GPU, external resource or input.
Candidate/auditor budgets are one each; retries/substitutions zero. Output path
must be absent. Construction tests and byte-compilation precede freeze.

From repository root, candidate once:

```sh
python3 -I research/analysis/task_memory_retrieval_7166_t0_host_a05_20261004/candidate.py
```

Only on exit 0, auditor once:

```sh
python3 -I research/analysis/task_memory_retrieval_7166_t0_host_a05_20261004/auditor.py
```

Post preregistration and freeze SHA to Issue #7166 before candidate execution.
