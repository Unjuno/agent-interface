# PR #8857 analyzer follow-up

Base PR head: `cd766747abb4ca6d321b626c0a7b9734b9e06816`.

## Finding

`_release_matches` compared release-side identity values by Python equality without requiring their wire types. A release receipt with integer admission deadline `1000` and release deadline `1000.0` was incorrectly accepted (`measurement_ready=true`, one hold). A pointer release with `button=true` was incorrectly joined to admission payload `1` for the same reason.

## Change and test-first evidence

Two regression tests were added before the implementation change. Against the PR head, both failed because the analyzer reported `measurement_ready=true`. The minimal fix now requires `type(valid_until_ns) is int` for the release deadline and `type(button) is int` for pointer release identity. The tests then pass and the admission remains unmatched when the release receipt is malformed.

## Verification

- CPython 3.11: analyzer 6/6 and owner-to-analyzer integration 1/1, in normal and optimized mode.
- WSLc, Linux amd64, Python 3.14.8, image `python@sha256:b9767f56a1cc620aa72d38cc3557d26412e38a4597c92953476136b78894ccbd`, network disabled, 1 CPU, 512 MiB configured: analyzer plus owner-to-analyzer integration 7/7 in both normal and optimized mode.
- `py_compile`, `git diff --check`, and all seven entries in the package SHA-256 manifest pass.
- WSLc reports swap cgroup support unavailable; memory was configured, but no swap limit is claimed.

The first WSLc invocation omitted `PYTHONPATH=/src/research/doom:/src`. The analyzer test imported its fallback stub and six cases failed with missing result fields; the owner integration case passed. This was an invocation error, not a code result. The corrected invocation with `PYTHONPATH` set passed all seven tests.

## Scope

This repairs synthetic per-key receipt validation. It does not add physical-input telemetry and does not establish key-up timing, GUI/game behavior, useful feedback, recovery, or MAP01 progress.
