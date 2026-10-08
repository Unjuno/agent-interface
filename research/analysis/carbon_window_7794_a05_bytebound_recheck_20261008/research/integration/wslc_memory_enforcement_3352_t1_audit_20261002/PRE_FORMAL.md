# Pre-formal construction and environment history

This file preserves every pre-formal issue; none of these events was a candidate/probe invocation or the formal audit.

1. The first local materialization used text-mode copies from GitHub. The independent checksum gate rejected the packet. Read-only inspection found the exact original `wslc-memory-t0/` packet in the shared workspace, whose four source hashes match its original manifest on both Windows and WSL. The published PR #6309 copies were retained separately; their byte/content differences are now explicitly recorded.
2. An early construction test used the text-mode copy and failed its source checksum. After pointing tests to the exact original packet, one command-mount predicate failed because it expected the placeholder path found in the published PR copy, while the original recorded command contains the exact absolute source path. The parser was corrected to validate a read-only `probe.py` bind while requiring both command paths to match. No experiment was run.
3. Final native WSL construction suite passed 6/6; see `results/construction/CONSTRUCTION.log`.
4. The first exact multi-mount readiness preflight exited 1 with WSL `E_FAIL` after approximately 39 seconds. No auditor executed. Read-only diagnostics: Ubuntu remained Running on WSL2; WSLc version and image inventory succeeded; `wslc container list` (running containers) returned empty; `wslc container list --all` returned E_FAIL. A separate no-mount/no-network smoke on the same pinned image printed `WSLC_SMOKE_READY`, exit 0.
5. After recording the incident and authorizing one mount-only preflight, the exact three-mount check returned `READY`, exit 0. Only then was the one formal auditor invocation run.
6. The audit container used `--rm`; post-run all-container listing showed only the untouched pre-existing exited smoke container `adadf5c4bd8d` (`ai-wsl301-migration…`).

No Docker Desktop process was started. The predecessor probe was never imported or executed by this successor.
