# Historical c1074 audit repair v2

The dependency-closure repair changed the packaged composition test from the historical freeze SHA-256 `3affd0aa2842d0b6ee47c2e0cb9bfe5a9239e69055347948a8a559612c2cd1f2` to `9413450c718f46dbce878fafc6e55ce53799d44bf4a1aeab8cdd406951d85217`. The v1 current-main auditor still hashes that mutable path against the old freeze, so it cannot revalidate the retained historical result on this package revision. The historical freeze, v1 auditor, raw, output, exits and audit result are unchanged.

V2 retains the exact historical test from commit `4ddcfd667c2cfef4d0801caefff3f006492ca03c` as `frozen_live_control/test_executor_v12_c1074.py.txt` (outside test discovery). It validates the original freeze against that snapshot and the vendored dependency closure, then checks the original raw/result and output/exit records. It reads no Git refs, performs no network operation and writes no files. Its stdout explicitly reports `current_main_continuity_checked:false` and `candidate_rerun:false`. It verifies historical artifact consistency, not the present source tree or execution.

## Validation

Run from the repository root:

```sh
python3 -B research/doom/map01_v39_partial_release_receipt_a02_20261005/audit_executor_v12_retained_c1074_v2.py
```

The v2 auditor passed 46 checks. A separate minimal 23-file fixture without `.git` passed; changing the historical source snapshot was rejected; removing the terminal F9 retry was rejected even after updating the result's raw hash. Both mutations were restored byte-for-byte. See `EXECUTOR_V12_RETAINED_C1074_AUDIT_V2.json` and `EXECUTOR_V12_AUDIT_V2_REGRESSION.json`.

`EXECUTOR_V12_AUDIT_V1_RECHECK_STOP.json` preserves the failed source-hash preflight and the diagnostic limitation: an earlier combined Git/auditor command was interrupted after returning no output, so it is not reported as a completed v1 audit. The later exact-parent snapshot read completed with a time bound and lazy fetching disabled. No candidate allocation was rerun. These checks do not claim real X11, application effect, live control, useful feedback, recovery efficacy, timing bounds, or gameplay.
