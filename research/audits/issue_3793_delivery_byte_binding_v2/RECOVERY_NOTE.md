# Recovery note — Issue #3809 allocation v3-02

Preserve this one-shot allocation as
`STOP_SOURCE_OR_FREEZE_MISMATCH`. Its two fail-closed construction tests
passed, but the auditor then stopped before the baseline or either mutation:
it looked up `PLAN.md` and `audit.py` by basename although the immutable freeze
uses full repository paths. The ten downloaded input hashes matched. No
baseline result or mutation outcome is claimed, and the allocation was not
retried.

The exact workflow source is archived under `source/` as inert evidence rather
than installed in `.github/workflows/`, avoiding another automatic run. The
predecessor v3-01 STOP is separately archived under
`../issue_3793_delivery_byte_binding_v1/`; the later successful raw-receipt
audit has its distinct scope and evidence under
`../issue_3793_raw_receipt_binding_v1/`. None of those outcomes upgrades this
STOP.
