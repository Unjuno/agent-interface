# A07 STOP — freeze commit failed before generator execution

Status: `STOP_FREEZE_COMMIT_FAILED_GENERATOR_RAN_UNFROZEN`.

Construction tests passed 3/3 normally and 3/3 under `-O`. A freeze document was prepared and `git add`/commit was attempted before the formal run, but Git rejected staging because the new A07 path was outside this worktree's sparse-checkout definition. The command sequence did not stop on that commit failure and proceeded to invoke the fixture generator once. It exited 0 and emitted 80,000 rows; stdout, empty stderr, and the generated fixture are retained.

Because the source was not committed/frozen when the generator ran, this output is exploratory custody only. Candidate and auditor were not invoked; no result, audit, or inference is available. The proposed freeze is retained verbatim as `FREEZE_ATTEMPT.json`, not represented as an effective freeze. No retry, alternate staging, or use of these observations in a later allocation will occur.

This is an execution/process-control STOP, not a scientific result. No participant, GUI, model, GPU, WSLc, Docker, network, or external data was used. Any future allocation must use a fresh path/seed and make freeze commit failure fatal before any generator call.
