# Correction — PR #5015 used the wrong auditor source

## Corrected provenance

PR #5015 was intended to retain diagnostic evidence for Issue #5006, whose
frozen baseline auditor blob is
`b314562f69633f2d4771d531ee747d7a856db2e4`.

The auditor actually executed in PR #5015 is blob
`1a6cc0e46b32d4cd6989aed118d003cce4cfe399`, the legacy #4733 auditor. It
was fetched from `research/analysis/predicate_order_drift_4258_v1/src/audit.py`
instead of the hardened #4994 baseline. This is a source mismatch, not a
minor path or labeling difference.

## Disposition

Do not interpret PR #5015's 336-row output, six boolean substitutions, or
manifest controls as verification of #5006's intended hypothesis. They are
observations against a different #4733 auditor only. The #5006 experiment
remains unverified; its allocation-01 execution is not repeated or relabeled.
The input archive/raw was correctly hash-identified, but that does not repair
the auditor-source mismatch.

The historical PR files remain byte-identical and unchanged. This file is an
additive correction for downstream reviewers and integration workers.

## Evidence references

- #5006 frozen target auditor: `b314562f69633f2d4771d531ee747d7a856db2e4`
- PR #5015 executed auditor: `1a6cc0e46b32d4cd6989aed118d003cce4cfe399`
- PR #5015 merged commit: `011912b1d2af1af31b3db0b826efadd73fe5cb3b`
- #5006 correction comment: `https://github.com/Unjuno/agent-interface/issues/5006`

## Recovery boundary

A valid follow-up must use the exact #4994 auditor and frozen tests/runner,
verify source and input identities before execution, and use a fresh additive
allocation/path. Preserve all prior STOP and diagnostic records. No such
follow-up result is claimed here.
