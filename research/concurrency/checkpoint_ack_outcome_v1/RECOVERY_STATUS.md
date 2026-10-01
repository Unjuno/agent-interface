# Recovery status: partial capsule, evidence-delivery HOLD

This directory preserves the exact 10-file subset present at the head of
`research/checkpoint-ack-outcome-3992-20260922`
(`2cff1bb669d4144c3f6dcb539883dc83fdba20b9`). It does not rewrite or pool the
two allocations described in Issue #4111.

## What is and is not present

The branch contains the plans/freezes/environment and only
`EVIDENCE.part000.b64` through `EVIDENCE.part003.b64`. The issue records the
capsule as **4/13 parts**. The exact remaining capsule parts, candidate and
worker source, formal rows, process receipts, raw-only auditor, original
failed control output, and read-only controls-v2 correction are not present in
this recovered tree. The existing partial fragments are retained unchanged;
they are not concatenated or treated as a complete archive.

Issue #4111 reports allocation-02 as a scoped PASS (90 cases, 915 audit
checks), while allocation-01 remains an immutable external-timeout STOP with
zero pooled rows. Those are historical Issue reports, not outcomes
independently reproduced by this partial package. No evidence here supports
promoting either allocation to a repository-reproducible result.

## Verification and disposition

- All 10 recovered source-branch files are preserved byte-for-byte by Git blob
  identity.
- The branch tree has only these 10 paths for this package; no uncommitted
  hidden capsule pieces were available in its Git tree.
- No formal case, worker, allocation, or control was rerun.
- The partial capsule is not decoded into substitute files and no missing
  source/raw bytes are reconstructed from Issue prose or hashes.

Disposition: `HOLD_EVIDENCE_CAPSULE_PARTIAL_4_OF_13`. A complete delivery
requires exact remaining parts and source/process/audit/control bytes, followed
by fixed-object restoration and an independent raw-only re-audit. Preserve
allocation-01 STOP and allocation-02 PASS as separate historical records.
