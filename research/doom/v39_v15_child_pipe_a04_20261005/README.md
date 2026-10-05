# V39-selected V15 child stdin construction A04

## Question and decision

The exact V39 `session_command()` selector opts into V15 for a measurement session. This construction tests whether that selected child can receive one delayed command through a real Windows anonymous stdin pipe while periodic scorer sampling and command dispatch stay on the session main thread.

A04 is a scoped pass: both frozen selector calls chose V15; the baseline child failed on Windows `WinError 10093` before command admission; the #7860 polling candidate exited cleanly, parsed one delayed `finish` command, and recorded four periodic samples. The command handler, polling owner, ready owner, and all sample calls reconciled to thread 42812. Windows text-mode CRLF left a trailing `\r` in the raw adapter line; the V15 JSON parser accepted it.

The first frozen audit's LF-only comparison failed and remains preserved in `AUDIT_V1_FAILURE.md`. The historical V2 audit and its first test attempt are preserved unchanged. The portable V3 audit pins Git blobs to immutable commit IDs and checks the retained streams, summaries, and freeze hashes without rerunning the child process. Earlier A01–A03 harness STOP notes are retained under `prior_stops/` and are not candidate failures.

## Reproduce the raw audit

From the repository root, run:

```powershell
python -B research/doom/v39_v15_child_pipe_a04_20261005/audit_v3.py
python -B -m unittest discover -s research/doom/v39_v15_child_pipe_a04_20261005 -p 'test_audit_v3.py' -v
```

The historical V2 unit tests can also be run from the package directory with `python -B -m unittest -v test_audit_v2`, but V2's audit script embeds its original external output-root assumption. Use V3 for the portable source and raw-output audit.

## Construction limits

This executed a real Windows child process and anonymous stdin pipe with exact V15 `main()` and adapter code. It executed V39's exact selector function, not the full V39 controller/planner. The child substituted inert V12 session, game, executor, and release-backend dependencies. No ViZDoom, real input owner, model, GUI, X server, OS input, task effect, recovery, latency benefit, gameplay, or MAP01 outcome was tested. This is integration-construction evidence only; it does not establish product integration or user-visible control success.

See `FREEZE.json`, `RESULT.json`, `AUDIT_V1_FAILURE.md`, `AUDIT_V2.json`, `AUDIT_V3.json`, the versioned audit scripts, exact baseline/candidate source snapshots, and raw child/scorer outputs under `results/`.
