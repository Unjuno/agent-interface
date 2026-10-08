# A04 execution and verification log

Candidate and auditor commands are recorded in `COMMANDS.txt`; the frozen
candidate ran once with exit code 0 and wrote `results/a04/RAW.json`. The
independent auditor ran once with exit code 0, found all 14 behavior checks and
all frozen hashes valid, and wrote `AUDIT.json` / `RESULT.json` with
`PASS_CONSTRUCTION`. Raw SHA-256:
`99b016b6e677a6938bbd012701842a5b70fdbbc6694a8040767e8f29fa9c7ac8`.

Verification on branch `research/59-tail-command-priority-a04-20261005`, based
on PR #7692 head `d59ce74c675294f2a4ba3ac7772442600deafecf`:

| Command | Outcome |
|---|---|
| Initial targeted regression before the fix | Expected failure: `deadline_overrun` returned instead of `command_ready`. |
| Targeted regression after the fix | 1 passed. |
| `python -m pytest research/doom/test_map01_scorer_stdio_adapter_v1.py research/doom/test_map01_scorer_stdio_adapter_v2.py -q` | 23 passed, 1 skipped (Windows anonymous-pipe select limitation). |
| First `test_session_map01_v18.py` attempt | 6 passed, 1 setup failure because the sparse checkout omitted `map01_overlap_controller_v39.py`, which the source-manifest test reads. No assertion contradicted the change. |
| `python -m pytest research/doom/test_session_map01_v18.py -q` after materializing that exact tracked source | 7 passed. |
| `git diff --check` | Exit code 0. |

The initial session-suite failure was an incomplete checkout; the required source
was read from the frozen commit and materialized unchanged before the successful
rerun. No candidate or auditor was repeated.
