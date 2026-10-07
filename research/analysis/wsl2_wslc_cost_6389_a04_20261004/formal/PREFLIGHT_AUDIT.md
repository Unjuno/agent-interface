# Independent verification of the WSLc gates

The raw `events.jsonl` contains three WSLc preflight receipts, one before each
candidate. A separate read-only verification checked all nine stdout/stderr
receipt hashes, all command exit codes, empty `container ls --quiet` outputs,
the pinned image ID in each image inventory and the same ID in each inspect
response. The three WSLc launcher stderr receipts all contain the cgroup/swap
warning. The running-container inventory was empty after the final run.

Disposition: **PASS — 3/3 idle/image gates and 3/3 warning receipts verified.**
No container or image was removed, and this check did not invoke a candidate or
auditor.
