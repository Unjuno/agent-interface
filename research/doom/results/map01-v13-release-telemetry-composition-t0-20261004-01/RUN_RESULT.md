# MAP01 v13 release telemetry composition check

Run ID: `MAP01-V13-RELEASE-TELEMETRY-COMPOSITION-20261004-01`

The single frozen WSLc invocation used the recorded pinned image with network disabled, read-only source mount, one CPU, and a 512 MiB memory limit. It returned exit code 1. Five `test_input_owner_v11` tests and two `test_session_map01_v13_release_telemetry` tests passed. The release backend test module failed during import because the pinned image does not contain Pillow (`ModuleNotFoundError: No module named 'PIL'`). Per the pre-run record, this candidate was not retried and no dependency was installed.

Decision: `FAIL/STOP` for combined composition. The v13 source-shape checks and v11 owner tests pass in this environment; the typed release backend and complete combined suite remain unverified. No game, X11, actual input, formal MAP01 allocation, useful-feedback, bounded-recovery, or matched-comparison claim follows from this run.

Evidence: `candidate.stdout.txt`, `exit.txt`, and `PRE-RUN.json` in this directory.
