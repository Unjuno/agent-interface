# Frozen WSLc invocation

Image digest: sha256:4b8e054511b1f3e3f4957ae657c20648f8e87312a75ebecafe2405bc6d852fd7
Source path in WSL: /mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-2/worktrees/win32-public-recovery-r43 (bind read-only)
Evidence path in WSL: /mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-2/worktrees/win32-public-recovery-r43/research/integration/standard_mcp_task_ledger_57_v1/current_main_wslc_xvfb_blocked_release_r05_20261123 (bind writable)

For each mode, use a fresh wslc run --rm --pull never --network none --cpus 2 --memory 4g --mount type=bind,source=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-2/worktrees/win32-public-recovery-r43,target=/workspace,readonly --mount type=bind,source=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-2/worktrees/win32-public-recovery-r43/research/integration/standard_mcp_task_ledger_57_v1/current_main_wslc_xvfb_blocked_release_r05_20261123,target=/evidence --tmpfs /tmp --workdir /workspace agent-interface-xvfb-mcp:late-input-r19 bash /evidence/run_probe.sh <mode>.
No retry is permitted. This WSLc CLI does not offer a read-only rootfs option; this packet does not claim one.
