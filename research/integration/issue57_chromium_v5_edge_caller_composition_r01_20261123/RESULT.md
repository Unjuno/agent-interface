# R01 result — STOP_SETUP_IMPORT

## Disposition

**STOP_SETUP_IMPORT; no Edge/browser task outcome.** The frozen test source at
commit `6cd3fe3ec74ea3f7c2cdc7cf5ea92635e0a0c73a` failed to import
`model_point_target_v1` because it attempted the module import before adding
`research/live_control` to `sys.path`. `unittest` failed during module loading;
the Edge process, loopback server, OCR worker, and task actions were not
started. This is a harness setup error, not a product or computer-control
result.

The initial shell wrapper also failed before launching Python because the raw
output directory did not yet exist. That wrapper failure and its correction
are retained separately. The corrected wrapper then reached the test runner and
captured the import failure above. No task allocation was consumed and no
positive or negative case is scored.

## Evidence

- Frozen protocol: [`PROTOCOL.md`](PROTOCOL.md).
- Python import failure stdout and exit 1: [`raw/normal.stdout.txt`](raw/normal.stdout.txt), [`raw/normal.exit.txt`](raw/normal.exit.txt).
- Earlier wrapper directory setup failure: [`raw/normal-wrapper-setup-failure.txt`](raw/normal-wrapper-setup-failure.txt).
- Frozen source commit: `6cd3fe3ec74ea3f7c2cdc7cf5ea92635e0a0c73a`.
- Static `py_compile` and `git diff --check` passed before this run; neither executes the integration path.

## Required follow-up

Keep this STOP unchanged. A separately frozen R02 may correct the import order,
recompute source hashes, and execute the same bounded two-case protocol once in
normal Python and once under `-O`. R01 provides no evidence for minting,
revalidation, browser input, task effect, generation refusal, or release.
