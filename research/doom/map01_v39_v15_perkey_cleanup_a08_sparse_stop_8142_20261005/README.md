# A08 sparse-checkout STOP custody copy

Copied byte-for-byte from closed PR #8142 (head `db8585bfc8c9806a0c3dadf7cc95a1d160c81858`) into a unique path because the canonical A08 directory on main contains a different successful A08 package from PR #8126.

The original A08 record documents one candidate-process invocation that stopped before treatment: a sparse worktree omitted `research/live_control/input_owner_v12.py`, causing `ModuleNotFoundError`. No fake-X owner, executor, key action, or raw candidate result was produced. The container image read also stopped separately. These records do not provide evidence for or against key-up retry.

Every original file, including its `SHA256SUMS` and source manifest, is retained with unchanged blob content. The manifest's listed basenames remain unchanged. This is historical custody only; no candidate or auditor was rerun.
