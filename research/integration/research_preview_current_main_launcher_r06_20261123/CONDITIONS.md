# Research Preview current-main launcher gate R06

- Base source: `1109a62ffd51ddf6888cc72be43a343f3ce0b550` (fetched origin/main)
- Host: Ubuntu WSL2, ext4, Python 3.12.3, Git 2.43.0.
- Checkout: fresh clean worktree before candidate test-only correction.
- Scope: read-only launcher boundary preflight plus real bash/exec fixture suite. No dependency install, browser/runtime/model acquisition, GUI action, or live golden task.
- Preflight: `python3 release/first_run_smoke_v1/preflight.py --root .`; status PASS_LAUNCHER_BOUNDARY, 18/18 checks, exit 0.
- Baseline suite: `python3 -m unittest test_launchers -v` and `python3 -O -m unittest test_launchers -v`; both initially failed 4/21 because tests omitted the explicit `--install-dependencies` flag required by current setup script.
- Candidate correction: test fixture now passes the explicit opt-in flag to its fake setup dispatcher; repeated staged failure tests clear only their disposable fixture venv before injecting the next failure.
- Candidate suite: same two commands; both passed 21/21 (normal 0.415 s, optimized 0.388 s).
- Preview bundle builder + supported-host acceptance helper suites: 11/11 PASS normally and 11/11 under Python optimized mode; raw logs retained.
- Raw logs preserve pre-fix failures and post-fix passes.
- Limitation: fixture contract only. This does not run setup, pip, doctor, GUI, model, live task, or supported-host golden acceptance.
