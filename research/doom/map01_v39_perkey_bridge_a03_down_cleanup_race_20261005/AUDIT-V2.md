# Corrected audit and retained outcome

The pinned Python 3.12.11-slim one-shot probe ran once with network disabled,
read-only source/root filesystem, 1 CPU, 512 MiB, 64 pids, and a tmpfs output.
Its retained raw trace shows baseline ordering
`input_cleanup_unscoped → input_admission → input_release_measurement(NOOP_ALREADY_UP)`;
the successor ordering is
`input_admission → input_release_measurement(CONFIRMED_PHYSICAL_UP)`. The
successor cleanup joins one owner release row, grants no authority, records no
application effect, and leaves no held keys. Exact environment, runtime image,
and command evidence are in `results/a03/RESULT.json` and `RAW.json`.

The first audit stopped on a digest-domain mismatch and remains retained as
`results/a03/AUDIT_V1_STOP.json`. The corrected audit v2 re-adjudicates those
same candidate bytes and records `PASS_DOWN_CLEANUP_RACE_REPAIRED` in
`results/a03/AUDIT.json`; its exact-type mutation tests run via
`test_a03_v2.py`. The source/test are separately bound by
`FREEZE-AUDIT-V2.json`. Do not rerun the consumed candidate probe to refresh
this audit.
