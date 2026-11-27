# Standard-caller Xvfb cancel-retirement failure — r07

This packet preserves the failing updated-head private-Xvfb run [39267303363](https://github.com/Unjuno/agent-interface/actions/runs/39267303363), PR #9194 head `fddd57729a05602c2f19dc3546c96067435e6b2c`. It contains the one-second withheld-ack baseline and four A-B-B-A ACK-immediate trials from the workflow artifacts. `SHA256SUMS` covers each copied JSON/PNG; r05 and the successful r06 remain unchanged.

The trace-2 ACK-immediate trial returned in 6.674 ms with `retired=false`, even though a later snapshot saw the process dead with exit `-15`. The Process trace shows `kill()` followed by `join(0.25)` returning in 0.053 ms, a 10 ms `join()` returning in 0.041 ms, and the child still reported alive; it exited about 0.284 ms after that final poll. This demonstrates that one `join(0.01)` does not necessarily wait for the OS process to finish. The replacement bounded-poll implementation and unit regression were added after this run; they are not tested by r07.

In the other four captured cases the exact owner was retired, but the separate release worker returned exit code 0 without a usable release result (`worker_did_not_exit_cleanly` / no horizon sample). The caller kept release `UNKNOWN`, `late_server_request_possible=true`, `task_success=null`, and replay denied. These are unresolved caller-cleanup outcomes, not verified key-up. The run is a failure and is retained as such.

This run used private Xvfb in GitHub Actions, no WSLc allocation. It does not establish physical release, product task success, MAP01, bounded recovery, or efficiency.
