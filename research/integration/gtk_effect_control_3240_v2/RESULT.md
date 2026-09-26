# Result — PASS_AUDITOR_SCHEMA_RECONCILIATION_SCOPED

This is a read-only re-audit of the historical #3240 `formal01` raw bundle; it
is not a new GUI allocation and does not alter `gtk_effect_control_3240_v1`.

## Findings

- The old auditor emitted two `native_execution_not_completed` errors because
  it read `raw_dispatch.result.execution.status`, which is absent.
- The retained receipt instead has
  `raw_dispatch.status=returned` and
  `raw_dispatch.result.status=completed`; the independent auditor now reads
  those exact raw fields.
- The positive row remains `adapter_status=partial` and
  `task_success=null`. Native program completion is not promoted to adapter
  task success.
- The corrected audit returns
  `HOLD_EVIDENCE_OR_EFFECT_BOUNDARY` with the sole finding
  `untouched_target_pixels_changed`. The original HOLD is preserved.
- Five local regression tests cover the historical disposition, corrupted
  action and preparation native receipts, a corrupted target image hash, and a
  measured-preimage hash tamper that attempts to hide the stability failure.
- The first local unittest invocation failed before running tests because its
  module import was not package-qualified. That harness error was retained and
  corrected; the rerun executed all three original tests successfully. Two
  review-driven corruption controls were added and passed as well.
- The first run after the review fix exposed an assertion still expecting the
  old unsuffixed error label; the auditor correctly emitted a stage-qualified
  label. The test expectation was updated and all five controls passed.

## Reproduction

From repository root, on the pinned local arm64 image used for this audit:

```sh
docker run --rm --pull=never --network none --read-only \
  --tmpfs /tmp:rw,size=64m \
  -v "$PWD":/repo:ro -w /repo \
  --entrypoint /bin/sh \
  issue4466-gtk-stability:formal-base-01 -lc \
  '/usr/bin/python3 research/integration/gtk_effect_control_3240_v2/audit_raw.py research/integration/gtk_effect_control_3240_v1/evidence/formal01 --out /tmp/audit-v2.json'

python -m unittest research.integration.gtk_effect_control_3240_v2.test_audit_raw -v
```

The auditor's expected exit is `2` for the preserved HOLD. No GUI input,
model/provider/network call, rerun, or artifact mutation occurred.

Source hashes for this additive auditor, its tests, preregistration and report
are in `SOURCE_SHA256SUMS`.

## Scope

This closes only the auditor schema-path defect for this retained bundle. It
does not resolve the XWD instability, complete #3240 or the eight-case #2606
acceptance, or claim application task success or production readiness.
