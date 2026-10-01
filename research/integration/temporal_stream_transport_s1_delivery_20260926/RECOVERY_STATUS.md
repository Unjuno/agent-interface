# Current publication status — Issue #4433

This file records the current GitHub-delivery boundary for the retrospective
local study described in `README.md`, `PLAN.md`, and `REPORT.md`. It does not
rewrite their historical local-result statements, supply missing bytes, or
change any predecessor allocation.

## Exact remote inventory

At the audited branch head `10e0e3ccb24d9b75a079f354104a5f81026d794c`, the
owned directory contains exactly these six files:

- `CONTROLS_BYTES_V2.json`
- `EVIDENCE_MANIFEST.json`
- `PLAN.md`
- `README.md`
- `REPORT.md`
- `restore.py`

The manifest declares nine files `EVIDENCE.part00.b64` through
`EVIDENCE.part08.b64`; none is present in that branch tree. The package also
does not contain the referenced `AUDIT.json`, original `CONTROLS.json`,
adapter/source members, or a complete original ZIP. Consequently the exact
archive cannot be restored or independently re-audited from the committed
GitHub bytes. The restorer was not invoked against incomplete inputs.

## Identity discrepancy and disposition

`EVIDENCE_MANIFEST.json` declares a 441,898-byte archive with SHA-256
`fa835b84dc9c8eeb8ed8bbc46ea72a91ab97c243aad7485c4b8aed1a818bb37e`. The
Issue's “Complete retention” text declares the same SHA-256 but 442,186 bytes.
Those byte counts conflict; neither is selected or silently corrected here.

The Issue-reported local disposition `PASS_WITH_VERSIONED_CONTROL_REVIEW`
remains historical and scoped, including its preserved first control-wrapper
failure and separately versioned byte-sensitive review. Repository-level
publication is **HOLD_MISSING_EXACT_SOURCE_AND_RAW** until the original bytes
are recovered and their parts, archive identity, restore, raw audit, and
controls are independently verified. No formal/X11 allocation was rerun,
replaced, pooled, or reclassified for this record. This does not repair the
predecessor `HOLD_OUTER_EXECUTION_RECEIPT_MISSING`.

This is an evidence-delivery status, not a scientific result, live-runtime
claim, or permission to rerun consumed work. Issue #4433 remains open.
