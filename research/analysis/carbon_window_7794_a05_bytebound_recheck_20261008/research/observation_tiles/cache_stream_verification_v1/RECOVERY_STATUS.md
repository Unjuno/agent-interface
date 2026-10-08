# Issue #4087 recovery status — partial-source archive only

Disposition: `STOP_SOURCE_PUBLICATION_BLOCKED`. This record preserves every
file currently available on the original remote branch
`research/cache-stream-verification-retained-20260922` at
`6848c48b8981ec2f277c59f222448c643b80889a`. It does not complete or validate
the original experiment's evidence bundle.

## Preserved content

The original 15 branch files are retained unchanged: plan, schedule, freeze,
environment, partial fixtures/evidence metadata, report, audit summary and
available audit/worker/test/source files. Existing `STATUS_NOTE.md` and
`HANDOFF.md` remain intact and continue to record the publication stop.

## Missing evidence and source

The Issue binds the complete original ZIP to 8,504,537 bytes and SHA-256
`5a321664e62dab7f8efd4490fea2a92954e176c627929a5667e4da43d50d035b`; that
archive and its large PNG/RGB primitive bytes are not in the branch. The PR
records the execution-source group (`make_inputs.py`, `run_batch.py`,
`execute_batch.py`) could not be published. The retained `test_study.py` also
imports absent modules. The observed first blocker is `vendor.image_artifact`;
subsequent imports require `legacy_candidate`, `png_oracle`, and
`vendor.exact_gate`, so this checkout cannot run the full construction suite.
No missing source, fixture, raw row, or receipt was reconstructed.

## Verification boundary

- The four available Python files syntax-compiled locally.
- The declared `test_study.py` suite was attempted and could not start because
  its required source modules are absent; this is a source-completeness STOP,
  not a scientific FAIL.
- Existing GitHub checks are delivery diagnostics, not reproduction of the
  reported 87-case / 525-publication outcome.
- Formal workers, timing, raw audit, and corruption-control replay by this
  recovery: **0**. The PR/Issue-reported `PASS_STREAMING_REUSE_CONTRACT_SCOPED`
  remains historical and unverified from this repository snapshot.

This is mergeable only as an explicitly partial archival/status record, never
as a complete reproducibility bundle or runtime promotion. Keep Issue #4087
open until the exact original source/raw archive is recovered and read back.
