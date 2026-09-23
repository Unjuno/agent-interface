# #1750 formal retention — audit integrity stop

Final disposition for the original allocation: **FAIL_INTEGRITY_AUDIT_GATE_COUNT**.

## First formal raw result

The one source-frozen 12-case allocation completed without execution errors and `RESULT.json` emitted `PASS_OPTIMISTIC_READWRITE_X11_TRANSFER_SCOPED` with all seven scientific gates true:

- allocation complete;
- all cases/cleanup complete;
- distinct mapped XIDs;
- independent-resource behavior correct;
- shared-global candidate behavior correct;
- surface-only unsafe discriminator exposed;
- external-stale behavior correct.

Descriptively, candidate stale effects were 0/3 and the surface-only comparator produced the preregistered stale G0 discriminator 3/3.

## Integrity stop

The **frozen preformal auditor** then returned:

`FAIL_INTEGRITY`, errors `["gates"]`.

The defect is deterministic and localized: `audit.py` requires `len(result["gates"]) == 6`, while the frozen formal intentionally emits **seven** gates. This is an auditor accounting bug, not a failed X11 case. Nevertheless the preregistered decision requires audit/integrity PASS, so the parent allocation is **not promoted as PASS**.

- formal invocations: 1
- reruns: 0
- replacements: 0
- tuning: 0
- raw parent rows pooled into a PASS decision: 0
- source postformal identity: 8/8 exact

The original failed audit is immutable evidence. Do not edit it into PASS or rerun the 12 X11 cases.

## Retention

The exact 12-row `FORMAL_ROWS.json` is retained losslessly as deterministic gzip + Base64 and can be restored with `RECONSTRUCT.py`.

- raw rows SHA-256: `230a7253f6b013a728feab0f8d5d3b75b12b9d1c47ddf0856b223b67e7b0fba8`
- raw RESULT SHA-256: `180f6a75a8ed2876cf93d5abfd0d07e4fe2d3b90f0a08db7d2fb481c7a554fa2`
- original failed AUDIT SHA-256: `dae25b7c69fed2d04236a02e1abf66230f1991f4803132d492b709eabae554b8`

## Successor rule

A successor may change **only the retained-audit accounting rule** (expected gate cardinality 6 -> 7), bind to the exact retained raw/result hashes, independently recompute every scientific gate from those immutable rows, and run corruption controls against the repaired auditor. It must not rerun, replace, or relabel this parent allocation.
