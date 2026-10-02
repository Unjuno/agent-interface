# Recovery status — Issue #4404

This is an archival recovery of the exact premeasurement source and gates from
the original branch, not a validation or promotion of its reported formal
result.

## Preserved source

- Original branch: `research/review-snapshot-read-20260926-c7r8`
- Original frozen source commit: `6ceab34676bc7f770b996ccb5af365c1811faffb`
- Original scope: the 21 committed files in this directory, copied without
  changing their contents.
- This recovery adds no runtime, workflow, index, predecessor, or production
  behavior changes.

## H / T / D / C / U

- **H:** the reported experiment compared one versus two image acquisitions
  while requiring canonical presentation-response equality. The Issue reports
  `PASS_SINGLE_ACQUISITION_PRESENTATION_SCOPED`; performance adoption was
  `NOT_ESTABLISHED`.
- **T:** the Issue reports six image-geometry/compression conditions, 126
  measured pairs, 252 calls, and a separate untimed controls block on a supplied
  Linux x86_64 / CPython 3.13.5 environment. This recovery ran no formal or GUI
  cases and makes no Docker/OrbStack attestation.
- **D:** the original branch contains the frozen source, plans, and gates, but
  does not contain the reported formal rows, process receipts, raw-only audit,
  or controls output. The reported outcome therefore remains historical and
  has not been independently reconstructed from repository bytes. No result
  is promoted by this archival PR.
- **C:** the frozen study is limited to synthetic fixed RGB/PNG inputs and an
  explicitly immutable retained artifact. Its source itself excludes mutable
  artifact compatibility, physical disk-I/O claims, host/model latency,
  token/bandwidth savings, and production adoption.
- **U:** exact formal raw/result delivery and independent repository-only
  re-audit remain outstanding. Issue #4404 stays open. Do not rerun or replace
  the consumed allocation to repair publication.

## Local recovery checks

The original source/test files are checked unchanged. Only the read-only
contract/unit suite and syntax compilation are run during this recovery; those
checks do not validate the missing formal outcome.

The full staged whitespace check flags five context-only lines inside the
preserved `CANDIDATE.diff`; those trailing spaces are part of the frozen patch
representation and were not normalized. The recovery status and all other
changed paths pass the whitespace check when that immutable patch artifact is
excluded.

The first unittest invocation from the repository root imported the checkout's
`runtime.cli_v1` instead of the frozen vendored namespace and stopped at import
before any test. Re-running from `/tmp` with the study and its vendored source
explicitly first on `PYTHONPATH` passed all six contract methods. Syntax
compilation of the study and vendored Python files also passed under local
CPython 3.14.5. The branch records CPython 3.13.5 for its reported formal
allocation; this local check is not an environment-matched replay.
