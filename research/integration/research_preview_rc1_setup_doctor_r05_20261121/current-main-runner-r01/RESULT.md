# Current-main supported-host runner recheck R01

Status: `HOLD_SUPPORTED_HOST_DOCTOR`. This is a recheck of the merged acceptance runner against the exact frozen RC1 checkout, not a Research Preview acceptance pass.

- Acceptance runner source: current main `a103a5ddb4fa12b8d7dde90b72f8655fafcfe3e5` (PR #10440 code is included; the runner itself was exercised from the Windows worktree through WSL).
- Target checkout: frozen RC1 `8e5052e04f8720fe89052ad01127114dd6852d88` at `/home/user/agent-interface-rp-rc1-doctor-r05-20261121`.
- Host: Ubuntu WSL2, Python 3.12.3; output directory was new and absent before execution.
- `preflight`: passed all 19 committed-tree/launcher checks.
- `setup`: correctly recorded `skipped_existing_venv` for the pre-existing RC1 venv; no dependency install command ran.
- `doctor`: failed 12/15. WSLg display and X11, Python imports, Windows Python and Windows Node passed. `windows_cli`, `chromium`, and dependent `codex_cli` failed because their configured paths were absent.
- The runner stopped after doctor failure, so `audit-retained` was not run. `--live` was not passed; no golden task, model call, GUI action, or allocation occurred. The default seed field is metadata only in this no-live run.

This establishes that PR #10440's existing-venv branch works in the frozen WSL environment and preserves the prior doctor HOLD. It does not establish the user-facing runtime gate. Raw stdout/stderr, step JSON, final report, host conditions and hashes are retained alongside this file.
