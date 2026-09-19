# OpenTTD compact verified evidence ABBA v1

## Result

A compact presentation of verified persistent-hover evidence retained the same
target-selection result while reducing reported input tokens in a fixed OpenTTD
comparison. Fixed Luna-low selected receipt 5 at source point `[485,51]` in all
four preregistered calls.

| Order | Presentation | Dimensions | Reported input tokens | Strict binding |
|---|---|---:|---:|---|
| 1 | full | 1280×1425 | 10,170 | receipt 5, `[485,51]` |
| 2 | compact | 640×334 | 8,274 | receipt 5, `[485,51]` |
| 3 | compact | 640×334 | 8,274 | receipt 5, `[485,51]` |
| 4 | full | 1280×1425 | 10,170 | receipt 5, `[485,51]` |

The compact mean is 1,896 tokens lower, a reduction of 18.64%. The PNG used by
the calls is 11,834 bytes versus 581,388 bytes for the full presentation. File
size is descriptive and is not the token metric.

## What changed

The full condition repeats the 1152-pixel source frame and five full toolbar
strips. The compact builder reads the already verified dwell observations,
checks each raw tooltip crop against its receipt pixel digest, and lays out only:

- the exact tooltip pixels, enlarged 2× with nearest-neighbour sampling;
- the receipt number;
- the receipt-bound source point.

The full source frame and pixels outside each tooltip are omitted. Original
receipts remain authoritative and the sheet grants no input authority. A
corrupted receipt digest is rejected before presentation.

The four calls used the same prompt, responder instructions, schema, model,
effort, receipt set and correct point. Only the image presentation changed. The
Full/Compact/Compact/Full order, hashes, gate and no-retry policy were frozen
before the calls. This is one planner model using Agent Interface evidence;
subagents are absent from the evaluated path and token accounting.

## Audit and limits

Windows and WSL independently reconstruct every model event, typed binding,
usage record, source hash and compact RGB image. PNG container bytes may differ
between Pillow builds, so the portable rebuild invariant is the decoded RGB
pixel digest. Both operating systems pass that invariant.

This is a fixed archived-evidence diagnostic for one OpenTTD toolbar task. It
does not establish served-model identity, monetary cost, latency causality,
dynamic-control savings, broad GUI reliability or human-tempo operation. The
next useful test changes layout or application while preserving the same receipt
contract, then measures whether compact evidence still preserves correctness.

## Reproduce

From `research/live_control`, after the archived prior evidence exists:

```sh
python3 preregister_openttd_compact_evidence_abba_v1.py
python3 run_openttd_compact_evidence_abba_v1.py
python3 audit_openttd_compact_evidence_abba_v1.py
```

The committed result is in
`results/openttd-compact-evidence-abba-01/`. Do not rerun the preregistration
over that directory; use a new study identifier for a replication.
