# WSL Fake X Calc proposal deadline and release composition replay

- Date: 2026-10-28 (Asia/Tokyo)
- Repository commit tested: bd377ab1b00a2376e2416d8b52976ebc8f25b704 (main after PR #9783)
- WSL distro: Ubuntu 24.04.3 LTS on WSL2
- Python: 3.12.3

## Scope

Replayed the current-main Calc G10 proposal timeout and native caller composition tests under Linux/WSL. The selected suite covers deadline/cancellation before and during snapshot copy, delayed callback completion after timeout, preservation of the completed prefix and verified empty key/button release, and refusal to dispatch a second input or publish an outer score after the late result. It also covers the successful fresh-alias receipt path and an unknown first effect stopping the suffix.

Both normal Python and optimized (-O) runs passed 10/10 tests. Exact output and exit status are retained in normal.log, optimized.log, normal.exit-code, and optimized.exit-code. The retained G10 interface raw.json hash is in raw-input.sha256. Current-main source blob IDs and the four unchanged support-module byte hashes are recorded in source-identities.txt and support-source-sha256.txt.

The transport and application effects are Fake X. This is Linux/WSL execution of a composed deterministic test; it does not open an X server, operate Calc, call OCR or a model, establish a new application task effect, or qualify Docker/WSLc live behavior. The support modules needed by the composition test are from the already reviewed scratch fixture identified by byte hashes; they are not silently represented as files in main. The main test package path was kept first, with only research.live_control.__path__ extended to that support fixture.

## Environment and setup record

environment.txt records the distro/kernel and isolated venv package versions. The venv is at ~/.venvs/agent-interface-goal; no repository dependency file or system Python installation was changed. Initial WSL attempts are retained in setup-attempts.txt: the first lacked Pillow; after installing test dependencies, MCP 2.x was incompatible with this MCP v1 code; pinning mcp<2 exposed the test's intentionally external G10 support-module dependency. The final two runs used mcp 1.30.0 and the path arrangement described above. A first raw python -m unittest attempt also printed Git's Windows CRLF files as modified under Linux; Windows Git subsequently confirmed the checkout clean before the recorded runs were repeated on this commit.

## Reproduction

From the repository root in Ubuntu WSL, with the recorded venv and support fixture available, run these exact commands: `~/.venvs/agent-interface-goal/bin/python -B research/integration/calc_g10_wsl_fake_x_release_20261028_r01/runner.py` and `~/.venvs/agent-interface-goal/bin/python -O research/integration/calc_g10_wsl_fake_x_release_20261028_r01/runner.py`. The runner is preserved in runner.py; output and exit status are the retained logs and exit-code files.

