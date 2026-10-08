# Supplemental read-only review audit

## Purpose and scope

This check addresses review findings against retained Issue #7722 T0 evidence. It reads the existing candidate raw JSON once and reconstructs all 18 case/policy runs. It does not execute or modify `candidate.py`, `auditor.py`, the original raw JSON, or the original audit JSON; it does not repeat the formal allocation.

The supplemental checker reuses the frozen auditor's job generator and structural checks, then independently reconstructs FIFO ready queues and mandatory control-first dispatch from frozen release times. For `shared_backpressure`, it independently derives which best-effort jobs should be rejected when the ready queue reaches its 64-job bound and compares that exact ordered list with the raw record.

## Reproduction

From this package directory:

```sh
python3 -m pytest -q test_review_regressions.py
python3 review_audit.py --output output/review/review_audit.json
python3 verify_retained.py
python3 -O verify_retained.py
```

The first command tests the original 18 raw runs plus policy and evidence mutations on in-memory copies. The second is the sole supplemental raw-only audit invocation. It records `PASS_SUPPLEMENTAL_RAW_RECONSTRUCTION`, zero raw reconstruction errors, eight rejected mutations, one accepted unchanged-trace control, zero candidate/frozen-auditor invocations, and zero retries. The last two commands verify package bytes and the supplemental record in normal and optimized Python.

## Result boundary

The stored supplemental result is SHA-256 bound to the unchanged candidate raw, cases, frozen candidate and frozen auditor, and supplemental checker. It corrects the policy-dispatch and backpressure gaps for this retained trace set, but it is not a new formal candidate/auditor allocation, does not independently establish the original six-mutation claim as originally executed, and does not establish host scheduling, GUI behavior, task effects, safety, or physical key release. The original `METHOD_PASS_SCOPED` is superseded pending independent human review; the frozen result artifacts remain preserved.
