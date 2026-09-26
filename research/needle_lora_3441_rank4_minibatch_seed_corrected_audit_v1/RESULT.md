# Issue #3887 independent audit — terminal result

## Decision

`STOP_INPUT_PROVENANCE`. The independent row-level audit was **not run**. The
pre-registered gate requires byte-verifiable frozen source and manifests before
scoring; that prerequisite failed. The original GPU allocation remains
`HOLD_LEGACY_COLLAPSE_NOT_REPRODUCED` and is neither rerun nor relabeled.

## What was frozen and checked

- Additive branch: `research/issue-3887-independent-audit-20260921`.
- Input snapshot: `main` commit
  `cb2445ad77d31b089eb4e43780b377c6eb054fd5`; the audit pins each input by Git
  blob and SHA-256. The preregistered audit/test sources were published in
  freeze commit `6025adda4ea338521542e2f262256fc637e6ea9a` before the one
  provenance-gate invocation.
- Five construction/corruption controls pass. An initial root-level unittest
  invocation exposed a module-name collision (`audit` resolved the repository
  package); the test loader was made sibling-file-specific before freeze, and
  the frozen suite then passed 5/5. The failed construction attempt is retained
  here; it was not a raw-data audit or a model run.
- Cached offline Docker image `python:3.11-bookworm` lacks PyTorch. No pull,
  install, network, training, optimizer step, model evaluation, or GPU use was
  made. The audit ran locally on CPU with `CUDA_VISIBLE_DEVICES` empty.

## Provenance evidence

The compressed raw payload itself verifies: envelope and sidecar decompress to
326,706 bytes with SHA-256
`27fb388f6f4b35ce9b460eb3fe3522b39def1c0193f5f07304b84257961eb51c`, matching
the retained envelope and metadata. The pinned reference baseline Git blob
also matches (`18b6be0a175df957d838e188de4c7ca826b26af8`). These checks do not
repair the following source/manifest contradictions:

| Evidence | Frozen/manifest SHA-256 | Current pinned Git-blob SHA-256 |
|---|---|---|
| `SOURCE_RUNNER.py` | `babbc44f868acc4eb159b71a0061ce9b57c690f2defbdbad885a7e828295e429` | `cc4126a2b144a8134930c69d02908af45bc8f44613ec5b7e856da13f9167d6f2` |
| predecessor `audit.py` | `a9cd15a6b322218a692dcd9e5fc03266a4ab7ddb3acd79d08def645813f29cfa` | `cdb8f3d80a031892ef701287801d22c3212af35f09c0a73d1f229f41f8edae8f` |

The retained `SHA256SUMS.txt` also begins with two non-manifest lines:
`Warning: truncated output (original token count: 250)` and
`Total output lines: 12`. Of its nine parseable entries, eight disagree with
the corresponding committed bytes: `AUDIT.json`, `FORMAL_METADATA.json`,
`FORMAL_STDERR.txt`, `SHA256SUMS.txt`, `SOURCE_3807_BASELINE.py`,
`SOURCE_RUNNER.py`, `TEST_CONSTRUCTION.py`, and `audit.py`.

The raw envelope remains available, but the frozen runner/auditor bytes and
published checksum manifest cannot be authenticated against their own recorded
pins. Accordingly `AUDIT_RESULT.json` records `audit_not_run=true` and no
scientific verdict. This is a typed provenance STOP, not evidence that the
numeric HOLD or raw predictions are false.

## H / T / D / C / U

- **H:** An independent CPU reconstruction could verify every retained row and
  reproduce the HOLD, if the source and raw bundle were byte-bound.
- **T:** One frozen provenance-gate invocation against the pinned main Git
  blobs. The gate stopped before scoring as preregistered.
- **D:** `STOP_INPUT_PROVENANCE`; no row-level metric/auditor PASS is claimed.
- **C:** No edits to #3887, PR #3894, the raw allocation, or its original HOLD.
  This branch is additive and audit-only.
- **U:** Whether all 160 curves, routes, sampler schedules, and summary
  statistics independently reproduce remains unknown until the exact original
  source bytes and a consistent manifest are available. No sampler-causality,
  task-effect, or runtime claim follows.

## Resume condition

Resume only when the original source bytes that match the recorded digests, or
an independently documented authoritative correction to those pins, is
available. Preserve this STOP and the consumed GPU allocation; do not rerun
training or amend predecessor artifacts.
