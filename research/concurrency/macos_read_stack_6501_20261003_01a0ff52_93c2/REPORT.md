# Native worker read-stack first result

The four-cell new allocation completed once after source freeze. On this selected macOS27.0.1/ARM64/CPython3.14.5 host, caller-close still returned EOF with the writer open after92 _Py_read/native-read-stub samples had already attributed the read to the exact owned worker. Wrapper-only cancellation left the native Future running at its252.05ms checkpoint. This narrows the entry-race interpretation of earlier6949, without proving kernel entry or portable termination semantics.

| Fixed actor | Native worker Python/read-stub weights | Primary native read | Writer at primary | Actual primary interval |
|---|---|---|---|---|
|reader_close|92/92|READ_EOF|OPEN|254.091916ms|
|normal_D|92/92|READ_DATA 0x44|OPEN|255.114125ms|
|writer_EOF|92/92|READ_EOF|EBADF|251.749458ms|
|wrapper_cancel|92/92|pending|OPEN|252.051708ms|

Each of four fresh owned peers/samplers exited0; a later exact owned-PID /bin/ps readback found all8 absent. All four executor threads were alive at the primary checkpoint and separately joined at final; all8 data FD lifetimes were then EBADF.36 literal events and16 IPC frames preserve actor/sample/primary/harness ordering. Harness D completes the wrapper native read only after primary; it is not attributed to cancellation. One observation per condition cannot establish an error rate, real-time bound, performance or portability.

Source commit14133b49d5b78fbe249a7ff4b2f4e56b2e827826/tree8470d3ce49cd13d74cc461b5351ce3d0585186fc and FREEZE201910d7... were fixed before producer17:49:45–17:49:52JST (08:49:45–08:49:52UTC). Formal producer/primary auditor1/1, retries0, actual exits0/0. Original result45381B/SHA39fe40ae06852687742b16daae59f49ed8d4d395c8be822e4c88a83dcd4279eb;17 frozen inputs and18 selected external pins remained unchanged after execution. OS/shared-cache/kernel transitive identity is incomplete. Original bytes remain private locally; published path-only derivatives have distinct original/public hash joins and do not authenticate inaccessible private bytes by themselves.

The first independently implemented saved-byte auditor PASS is retained. Subsequent12 synchronised corrupted-copy checks reject9 but reveal3 false accepts: integer1/0 executor states and boolFalse sampler exit, due Python value equality. Versioned posthoc auditor_v2 adds strict types, keeps original thresholds and rejects the exact same12 copied result hashes; retained original result still yields the unchanged4 conclusions. It is a data-only correction, not a second primary audit or OS producer/formal allocation replay. The first failed controls and full copies remain in the inert capsule. Control per-command PID/start/end were not separately persisted; actual tool argv/exits and JSON UTC/source/copies are retained, unlike the complete formal supervisor receipts.

Excluded C01 construction is separate: main stdin has84 sampled read frames, designated worker84 condition-wait frames. Ten saved construction copy controls refuse wrong attribution/types/counts. One copied main block renamed for independent parser exercise is explicitly not a native worker observation. Original first setup/observation-path failures are in PREPARATION; no source failure was hidden or turned into a formal retry.

Adoption: retain this scoped platform-boundary evidence. No cancellation runtime implementation, kernel-trace guarantee, GUI/application/task/model/scorer result, physical release, efficiency or total deadline is established. Earlier6949 allocation/raw/decisions stay unchanged; other shared runtime owners are separate; main is untouched. All sources are inert .py.txt snapshots, no workflow/discovery entry.

[Protocol](PROTOCOL.md), [source freeze](FREEZE.json), [summary](RESULT_SUMMARY.json), [literal first public result](raw/result.json), [first audit](raw/audit.json), [formal supervisor](supervisor/RUN.json), [first failed saved controls](posthoc/result-controls-first.json), [v2 saved controls](posthoc/result-controls-v2.json), [full first copied data capsule](posthoc/first-controls-public.tar.gz), [projection joins](PUBLICATION_ORIGINS.json).
