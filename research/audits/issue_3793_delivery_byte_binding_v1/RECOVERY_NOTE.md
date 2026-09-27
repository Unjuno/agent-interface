# Recovery note — Issue #3793 allocation v3-01

Preserve this allocation as `STOP_SOURCE_OR_FREEZE_MISMATCH`; it is not a
baseline PASS/FAIL and is not the later raw-receipt binding audit under
`issue_3793_raw_receipt_binding_v1/`.

The frozen check stopped before the baseline because the manifest's
`audit_plan` digest omitted `15` from the expected SHA-256. The first run's
preliminary mutation fields are retained verbatim in `result/STOP-01.stdout.jsonl`
but are inadmissible because the source gate had already failed. The pull
request workflow was unintentionally triggered a second time after a STOP
artifact update; both run IDs and the automation deviation are recorded in the
original issue/PR history. No further invocation is authorized or claimed.

The original workflow definition is retained under `source/` as inert evidence;
it is deliberately not installed under `.github/workflows/`, so recovery cannot
dispatch it again. The subsequent #3793 audit work has its own frozen inputs,
outputs, and scope in `issue_3793_raw_receipt_binding_v1/` and the open PR
#3818. Neither successor changes this consumed STOP.
