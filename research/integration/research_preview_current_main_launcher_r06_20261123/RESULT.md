# Result: Research Preview launcher gate R06

The frozen current-main launcher preflight passed 18/18 on a fresh clean WSL2/ext4 worktree at `1109a62ffd51ddf6888cc72be43a343f3ce0b550`. This is only the POSIX launcher byte/mode/syntax/pin boundary.

The existing 21-case launcher test suite exposed stale setup-caller assumptions: four cases invoked setup without `--install-dependencies`, while the current script correctly refuses dependency installation unless that explicit flag is supplied. Once the fixture supplied the opt-in flag, three staged failure tests also exposed cross-case leakage of a fake `runtime/.venv` inside the disposable fixture. The test now removes that temporary fixture venv before each injected setup failure. Production files and pass criteria were unchanged.

The corrected suite passes 21/21 normally and 21/21 with Python `-O`. The before/after stdout logs and preflight JSON are retained under `raw/`; `SHA256SUMS` covers them.

This does not establish supported-host setup/doctor, fresh no-retry golden task, `audit-live`, GUI behavior, runtime distribution acceptance, live provider behavior, or Research Preview graduation. Keep #58 open.
