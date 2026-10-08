# T1 result — one-shot check/claim race

## Result

`PASS_HOST_ONLY_RACE_BOUNDARY` within the declared same-process thread fixture.
The synchronized baseline produced **2 candidate / 2 audit callbacks** with
both callers returning 0. The atomic-claim control produced **1 candidate / 1
audit callback**, with statuses `[0, 2]`; one caller obtained the reservation
and the other was rejected before dispatch. The independent raw auditor
returned `errors=[]`.

This confirms that `invoke_allocation.run_one_shot`'s separate marker check and
`START.json` write admit duplicate work if both callers pass the gate first.
`race_guard.run_reserved` demonstrates a local exclusive-file-creation claim
that closes this exact window. The permanent claim is fail-closed after a crash
and may strand an allocation; availability/recovery policy is not tested.

## Execution and provenance

- Runner: `python run_experiment.py results/raw.json` (one execution, no retry).
- Independent audit: `python audit_race.py results/raw.json results/audit.json`
  (one execution after runner success).
- Focused tests: `python -m unittest -v test_race_guard.py test_audit_race.py`;
  **7/7 pass**. `py_compile` passes for all five Python files.
- Executed at `2026-09-30T17:48:13.115470+00:00`.
- Experimental branch HEAD: `77cf3922edfa88785d6b8d13abf7f1a3fce623b2`;
  observed main: `c043e25202db0c54ca43ec5cb4b78dbbf0fb888f`.
- Baseline guard SHA-256:
  `dad0c6205b69e691e33d40be5260f844bd4f9bc2a10e449d05d7fb69004cd9aa`.
- Atomic-claim prototype SHA-256:
  `4c6849091986efa306f070cf4b2acf1e12c72c045a001142b8661c1867f03efa`.
- Raw SHA-256: `3d83802dc746c556cfdb2539159880b39d690eb7a5f862d8add6bb8c39d87e4c`.
- Independent audit SHA-256: recorded in the package manifest.
- Docker/container invocations: 0. X11/input invocations: 0. Model calls: 0.

## Scope and next implication

The baseline uses a deterministic two-thread barrier after gate evaluation;
the control starts two threads together and contends on one NTFS temporary
directory. This does not establish a separate-process or multi-host result,
network filesystem semantics, or a product launcher fix. The implementation is
a research prototype in this analysis package; the frozen Allocation 06 source
and STOP record are untouched. Any future live allocation must use a new
current-main freeze and explicit non-overlapping resource assignment.
