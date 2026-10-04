# A02 candidate run record

**Run:** `v39-session-child-pipe-a02-20261005` on 2026-10-05, Windows 11
desktop, CPython 3.11.9. The frozen command was:

```powershell
py -3.11 run_pipe_a02.py --source-tree 22615a96e2166619933cd7fb375fc612ec30579d
```

The runner extracted the exact `emit`, `reader`, and `wait` ASTs from the
source blobs pinned in `FREEZE-A02.json`. It launched one Python child with a
real stdout pipe, sent the frozen 2,249-byte A08 `input_released` event, and
saved the child writer logs, stdout bytes, controller-received JSON, result,
and process receipt under `results/a02/`. Candidate exit was 0; one event was
written and received; both per-key measurements remained; authority was false;
stderr was empty; the reader thread joined. The captured command output is
`CANDIDATE_A02_STDOUT.txt`.

The candidate result took 11,067,500 ns from parent setup through pipe read and
closure for this one synthetic local event. This is a single construction-run
duration, not a latency estimate or performance claim.

Audit V1 failed on a hash-map assumption; audit V2 returned `FAIL_AUDIT` after
checking the wrong receipt fields. Both outputs are preserved. Audit V3 reads
the actual frozen result layout and returns `PASS_AUDIT` without rerunning the
candidate. See `AUDIT_A02_V3_PROTOCOL.md` and `AUDIT_A02_V3.json`.
