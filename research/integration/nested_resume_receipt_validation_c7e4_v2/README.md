# Strict resume-receipt validation: retained engineering evidence

Refs #4307. This delivery does not close that Issue or change its separately owned
48-case nested-frame allocation. No shared runtime, workflow, index or product
behavior is promoted. All paths in this delivery are additive to the intake main.

Two distinct results are retained:

- **PASS_LOCAL_ENGINEERING_CHECKS**: the preceding conversation's locally frozen
  6,653-request receipt-validation correction, published retrospectively here.
- **PASS_ENGINEERING_X11_RECEIPT_COMPOSITION**: 12 source-first private Tk/Xvfb
  construction cases connecting the unchanged legacy/strict gates to actual XTEST
  suffix input. This is an engineering smoke, not a formal efficacy experiment.

See REPORT.md for H/T/D/C/U, chronology, counts, failures and limits. The original
partial nested-resume pilot remains STOP; its full 264 files are owned separately
by #4307 and remain in the original supplied conversation ZIP. They are NOT part
of this capsule. Every one of the correction's original 65 files is included.

## Read-only reproduction

From this directory, using Python 3.13 standard library (no display/model needed):

```sh
python -B verify_publication.py
python -B -m unittest -v test_publication
```

The first command restores 162 exact files in a fresh temporary directory, verifies
every restored byte hash, runs only the retained read-only audits/unit checks and
requires byte-identical audit/control output. It never starts an evaluation worker,
X server or GUI study. Expected summary: PUBLICATION_CHECK.json.

To inspect source/raw files without executing any restored code:

```sh
python -B verify_publication.py /tmp/receipt-review-ABSENT
```

The destination must not exist. `retained/` contains all 65 original correction
files. `smoke/` contains the new source, frozen plan/environment, both six-case
batches, launcher receipts and raw-only audit. `construction01/` and
`construction02/` preserve prefreeze setup/auditor incidents. Never rerun consumed
allocation runners to repair an evidence-delivery issue.

## Exact storage contract

EVIDENCE_MANIFEST.json binds 13 Base64 parts and the 74,468-byte XZ archive:
`fa58e936cafb1dc639db62ff44604f8dfc98583b721a225fc6c88abdde8f5227`.
The restored 162 files total 8,905,972 bytes. Three canonical JSONL streams are
stored as columns of their actual retained values, preserving presence separately
from null; other members are stored as exact bytes. Decoding runs no candidate or
oracle and regenerates no experimental outcomes. Every reconstructed file must
match its original byte count and SHA-256. This is a lossless storage transform,
not sampled rows or a summary substituted for raw evidence.

The restorer validates bounds, canonical relative paths, unique members, storage
kinds and output hashes before writing; it refuses an existing destination. Eight
packaging-only corruption/overwrite controls pass. It assumes a trusted fresh
local destination and does not claim authenticity or protection against a hostile
concurrent filesystem writer.

## Source-first boundary

New smoke freeze commit: `975a0b0399b5e6a7a034945304c9dbfa65aa5e19`.
SMOKE_SOURCE.tar.xz.b64 and SMOKE_FREEZE.json were read back before case 0. Source
capsule Git blob: `a30cc00c4d841843227a2ff9e3f49863c4b05789`; decoded XZ SHA-256:
`09837bff4573864f6b4da54abd402be9c6d0fe462f2c171facdb3238867d5ef5`.
The old 6,653-request check was NOT publicly preregistered; this later freeze does
not change that chronology. The two result classes must never be pooled.
