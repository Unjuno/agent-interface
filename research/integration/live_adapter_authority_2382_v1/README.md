# Live adapter authority receipt v1 (#2382)

Status: PREREGISTERED / no authority provisioned / no live allocation

This additive path freezes the minimum auditable receipt required before Issue #2337 may allocate a live Chromium-to-CLI adapter run. It does not grant authority, read credentials, invoke a provider, open a GUI, emit input, or modify retained V5 evidence.

## H — hypothesis

An explicit, scope-limited receipt can distinguish an authorized live allocation from mere environment presence and keep the existing preflight fail-closed.

## T — admission

A candidate receipt must validate against `authority_receipt.schema.json` and include:

- named principal and purpose;
- provider/model/effort;
- disposable Linux/X11 Chromium scope;
- independent scorer and retention location;
- release owner and verification responsibility;
- the exact source-preflight identity and status.

Only `status=DECLARED` may proceed to a separately reviewed live runner. ABSENT, EXPIRED, REJECTED, malformed, over-broad, or missing receipts must remain HOLD/STOP with zero model, GUI, input, and network task calls.

## D — result contract

The live runner must retain the validated receipt beside model attempts/usage, observation and frame hashes, lifecycle rows, guarded dispatch/refusal/repair, delivery decision, independent effect score, cleanup, and release receipts. The receipt is provenance, not evidence of task success.

## C / U

This schema is one preparation contract for one Linux/X11 Chromium fixture. It does not prove provider authority, model utility, GUI correctness, effect correctness, latency, token savings, held-out transfer, or production readiness. The actual live experiment remains Issue #2337 and must preserve its frozen V5 control and changed-target failure.

## Stop rule

No receipt means `HOLD_NO_MODEL_AUTHORITY`. Do not infer authority from credentials, process exit, environment variables, or a successful source preflight.
