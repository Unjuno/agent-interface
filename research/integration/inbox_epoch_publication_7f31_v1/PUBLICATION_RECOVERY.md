# Issue 3938: exact-byte publication recovery (2026-09-22 JST)

## Current disposition

The original raw-publication HOLD recorded in REPORT.md and PUBLICATION_STOP.md is historical and remains unchanged. This additive recovery supplies the complete original formal raw and full original audit, allowing a GitHub-only reader to revalidate the frozen allocation. No formal case was rerun, replaced or relabelled. This is evidence delivery, not a new scientific result or runtime promotion.

The uploaded original conversation ZIP is 452737 bytes, SHA-256 `3604cd9e56d7446b58f4e2636876cbe7155ce01dad501ac2b68b573dde9c2fd5`. Its 584 retained entries passed the original archive verifier. Extracting it and invoking the unchanged raw-only auditor reproduced the original AUDIT.json byte-for-byte. The actual environment remains the provided Linux x86_64 / CPython 3.13.5 execution container; Docker CLI is absent. No Docker/OrbStack replication is claimed.

## Exact retained bytes

`published/RAW.00.b64`, `.01.b64`, `.02.b64` concatenate to Base64 of an XZ-compressed original raw JSON. `published/AUDIT.b64` is Base64/XZ of the full original audit output. All four GitHub-created blob IDs equal the local expected blob IDs recorded in restore_evidence.py. These are lossless transport encodings, not summaries.

- raw.json: 288509 bytes; SHA-256 `eef12b6de49f12f34cc86dca0dcea0d66986ed739d9cfc3adf640c966b6a403a`.
- AUDIT.json: 8138 bytes; SHA-256 `b1625376ee177f8654f6053d8768117f4fcafe6169eefa5e62da9cec9dbe3766`.
- Original frozen source, PLAN.md and FREEZE.json remain unchanged and are checked by the restorer.

The restorer verifies every part, caps decompression memory/output, validates both final SHA-256 digests and refuses an existing output directory. It executes no runner, model, GUI or action. A local clean-directory restoration passed; the frozen auditor exited 0 and its stdout exactly equalled recovered AUDIT.json; existing-directory restoration refused with exit 2. Separate historical construction and per-case filesystem copies remain in the original ZIP; all 45 formal case evidence records, raw worker output, fixture bytes, identities, exits and source receipts needed by the frozen raw-only auditor are now in the published raw. The ZIP itself is not claimed to be on GitHub.

## Revalidate from a checkout

Use a genuinely new output directory. Run from repository root:

```bash
python -S -B research/integration/inbox_epoch_publication_7f31_v1/restore_evidence.py /tmp/issue3938-audit-new
python -S -B research/integration/inbox_epoch_publication_7f31_v1/audit.py /tmp/issue3938-audit-new/raw.json > /tmp/issue3938-audit-new/REAUDIT.json
cmp /tmp/issue3938-audit-new/AUDIT.json /tmp/issue3938-audit-new/REAUDIT.json
```

Do not run run.py to repair a publication failure. AUDIT_SUMMARY.json remains a derived summary; TRANSPORT_FAILURES remains quarantined. Independent audit means separate code/process authored by the same assistant, not external replication. The scoped result remains 45 cases; caller-ID-only 6 cross-generation cases, sidecar-precheck 3, PIN_ONCE 0; all 90 worker exits zero and all 9 corruption controls rejected. Coherent historical notification is not fresh action authority or model consumption.

Main integration and PR checks must be confirmed separately after publication; this document does not assume a merge. #3876 and the full ROADMAP remain open. Concurrent #3978 owns retained-file reclamation and #3977 owns whole-stream byte budgets; neither allocation is rerun here.
