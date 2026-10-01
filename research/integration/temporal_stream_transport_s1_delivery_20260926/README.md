# Retrospective temporal stream transport evidence

This directory publishes an already executed local study. It is **not** GitHub preregistration and does not rerun the consumed evaluations.

Scoped result: `PASS_WITH_VERSIONED_CONTROL_REVIEW`. The 72 normal stream trials and 12 malformed-input trials are retained. The first corruption-control wrapper mistake (Python bool/int value equality) remains preserved; `CONTROLS_BYTES_V2.json` is the separately named byte-sensitive review and does not overwrite the first failure.

The nested predecessor X11 allocation remains `HOLD_OUTER_EXECUTION_RECEIPT_MISSING`; this publication does not invent its missing outer process receipt.

Complete original delivery ZIP SHA-256: `fa835b84dc9c8eeb8ed8bbc46ea72a91ab97c243aad7485c4b8aed1a818bb37e` (441898 bytes). It expands to 329 files / 2491956 member bytes.

Restore (data-only):
```sh
python -I -S -B research/integration/temporal_stream_transport_s1_delivery_20260926/restore.py /tmp/temporal-stream-s1-review
```

See `PLAN.md`, `REPORT.md`, `AUDIT.json`, `CONTROLS_BYTES_V2.json`, and `EVIDENCE_MANIFEST.json`. Do not invoke any historical live X11/formal runner from the restored archive.
