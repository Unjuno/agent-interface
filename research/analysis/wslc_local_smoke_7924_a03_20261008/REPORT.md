# A03 report — failed independent audit attempt retained

## Result

`FAIL_AUDITOR_CONTRACT`. The one pre-frozen WSLc run exited 1 with `KeyError: 'absence_verified'` in A03 `validate_cleanup`. A02's candidate cleanup receipt has a top-level `absence_verified`, but its auditor cleanup receipt stores the verified absence under `targeted_inspect_checks[1].absence_verified`. A03 incorrectly applied one record shape to both roles.

The failure occurred before A03 completed its baseline validation, before mutation controls ran, and before `AUDIT.json` could be produced. Therefore this allocation establishes no independent A02 audit pass. It does establish that the frozen A03 command ran once in WSLc 3.0.1.0 with the pinned cached image, `--network none`, a read-only mount, `--pull never`, and `--rm`; the requested 512M is not an effective-limit claim because WSLc warned that swap-limit/cgroup support is unavailable. The exact CID was inspected once and was absent after auto-remove.

## Preservation and non-actions

- A02's branch, issue, files, `FAIL_AUDITOR_CONTRACT`, and candidate success record are unchanged.
- A03 source was committed before the sole invocation; the failure trace, CID, cleanup receipt, and run context are retained here.
- No candidate rerun, A02 auditor rerun, A03 retry, Docker action, image pull, global container list, or operation on unrelated containers occurred.

## Scope

No claim about Docker parity, speed, memory relief, hard memory enforcement, OOM prevention, or general migration. This failed audit allocation must remain distinct from A02 and any later successor.
