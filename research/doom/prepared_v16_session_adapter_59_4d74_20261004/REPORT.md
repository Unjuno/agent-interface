# Prepared relay + V16 session selection (construction)

## H/T/D/C/U

- **H**: The prepared portable relay fixes the v39 controller/app-server host boundary, but the frozen v39 `session_command()` still selects `session_map01_v12.py`. A narrowly scoped selector adapter can preserve the v39 runtime argv while selecting current-main V16.
- **T**: Read the exact relay adapter, relay runner, frozen v39 `session_command`, current-main V16/V15 sources, and source08 closure. Add a pure argv adapter and fixture-only tests. No process/session/controller/model/game/input launch.
- **D**: `python3 -m unittest -v test_session_command_adapter.py` and `python3 -m py_compile session_command_adapter.py test_session_command_adapter.py`; expected contract is exact preservation of `--out`, `--seed`, `--timeout-seconds 600`, `--skill 1`, and fixture manifest, with only the session path changed to V16.
- **C**: This tests command construction, not a runnable relay integration, source custody, container execution, live app-server behavior, scorer efficacy, or any gameplay/release claim. The relay runner itself has a hard-coded source08 mount and Windows host paths; source08 drift is 5/54 files (4 changed, 1 missing) against current main `93090bcbf0c9eb0cd5f6feeb4abd2477e8453202`. The adapter must be integrated only with a refreshed closure and authorized allocation.
- **U**: A new relay revision/config surface that chooses a refreshed source closure and this adapter; then isolated container construction; then independent review and separately authorized live lane. No retries/launches until those conditions are met.

## Executed result (2026-10-04)

- Native macOS Python 3.14 fixture-only run: **PASS, 3/3 tests**, 0.002 s. Covers V16 selection plus exact legacy runtime flags, rejects wrong/missing session paths, and verifies installation leaves app-server and path-conversion hooks unchanged.
- `py_compile`: **PASS** for both files. `git diff --check`: **PASS**.
- First test attempt: **FAIL, 1/3**, because `Path.resolve()` canonicalized temporary paths from `/var` to `/private/var`; the expected paths were corrected to compare canonical values. Rerun above passed. No production code behavior was weakened.
- Container/live: **NOT RUN** by design. The source08 drift and runner's pinned source08 mount make a container run against that closure non-representative of current main; no host CLI, app-server, controller, game, model, or input was launched.
- Result class: **PASS_CONSTRUCTION_ONLY**. It does not establish that the adapter is wired into `portable_controller_entry_03.py` or `run_controller_relay_03.py`; that remains the next integration step after refreshing and pinning the complete source closure.

## Scope boundary

This is an additive, construction-only successor. Historical source08 and predecessor result packages are not edited or regraded. The V16 candidate is current main only; draft PR #7551 is not treated as merged evidence.
