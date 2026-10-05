Candidate command (one invocation):
`wsl.exe -d Ubuntu -- bash /mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-6/outputs/x11-xtest-device-cross-client-a01/run.sh`

Outer command exit: 1. The captured error was a post-candidate destination-copy failure; see `RUNNER_WRAPPER_DISCREPANCY.json`. The inner frozen runner recorded candidate exit 0 in `wrapper_exit.txt` and `run_wrapper_exit.txt`.

Candidate stdout: `{"candidate_exit": 0, "raw": "/home/user/x11-xtest-device-cross-client-a01-20261005/results/a01/raw.json", "sha256": "7e98e0e8766d0d3ebf85c03b2965236d098799e1740fa1b43426950dde0a0a8e", "status": "CANDIDATE_COMPLETE"}`

Auditor command (one invocation, after candidate exit and raw hash verification):
`wsl.exe -d Ubuntu -- python3 -B /mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-6/outputs/x11-xtest-device-cross-client-a01/audit.py --raw /mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-6/outputs/x11-xtest-device-cross-client-a01/results/a01/raw.json --out /mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-6/outputs/x11-xtest-device-cross-client-a01/results/a01/AUDIT.json`

Auditor exit: 0; verdict `DEVICE_PATH_DOES_NOT_ISOLATE`; checks 30/30.
