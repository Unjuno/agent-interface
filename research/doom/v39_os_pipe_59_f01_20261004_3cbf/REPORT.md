# F01 first real subprocess OS-pipe boundary

Freeze9f5f4780e24bb6c76fa0ada185bd95f92eb06282, fixed transferred archive
a2d6554714c7cfd7583dc0e166d79eee9a1639dbebcb43ea2f284251962af54f
host/guest equal. Historical E02 sourcearchive verified before first run
d1ad6dcb8720b27766702361b4898d13259d2efe0b173e7d0fbc970fe3d988db;
each exact reader snapshot hash verified by frozen probe before child start.
Own private VM research-6183-t0-20261003 had no running Docker containers.
Image sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b.
Docker configured UID501/netnone/CPU1/1GiB/swap0/pids128/capdropALL/read-only
source/root with isolated tmpfs and fresh output. F01 does not sample cgroups;
configuration alone is not a new proof of enforcement.

First container f01-real-pipe-formal-3cbf-20261004 State:
```
{"Status":"exited","Running":false,"Paused":false,"Restarting":false,"OOMKilled":false,"Dead":false,"Pid":0,"ExitCode":0,"Error":"","StartedAt":"2026-10-03T22:45:04.310762347Z","FinishedAt":"2026-10-03T22:45:05.314215012Z"}
```
Command python3 -B /experiment/probe.py /source.tar.gz /out/record.
All4freshcells executed once/model0/retry0; raw fiveJSONfiles retained.

| Case | Outcome | Cause | Reader alive | Child alive | Unhandled |
| --- | --- | --- | --- | --- | --- |
| original_fault | TimeoutError | none | false | true | JSONDecodeError |
| candidate_fault | _SessionReaderFailure | JSONDecodeError | false | true | none |
| candidate_healthy | ready | none | false | true | none |
| candidate_eof_alive | TimeoutError | none | false | true | none |

Each child used actual stdout PIPE with UTF8 TextIO, emitted the frozen literal,
flushed, closed FD1 and stayed alive3s; measurement observed childalive before
owned cleanup terminate, cleanup exit-15 each. Healthy exactready event delivered
despite subsequent EOF. Original malformed pipe silently kills reader relative
to wait; candidate surfaces parsercause. PASS_SCOPED_OS_PIPE_PARSER_NOTIFICATION.
EOFalive remains HOLD_UNSURFACED_EOF: no readererror or failure notification.
No recovery candidate is implemented or adopted here.

Measured wait intervals do NOT identify pipe-to-notification latency: data may
already have been parsed before wait_start (candidate interval43,083ns).
No statistical/causal comparison. Literal emission script retained, but no
separate pipe-byte tee; exception document/OS scheduling are not independently
recorded. No GUI/input/cancel/game/controller/model/task-effect evidence.
E05 native result is unchanged and not repeated. F01 only extends transport
boundary evidence and exposes a live-child EOF gap. Independent result review
and integration checks pending; whole #59/roadmap remains open.
