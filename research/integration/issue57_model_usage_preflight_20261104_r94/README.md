# R94 — Windows Calc artifact identity regression

## Finding

On the current Windows host, the existing integrated Fake App Server → public MCP → owned Calc → saved-FODS scorer test returned `artifact_missing_or_unstable` even though `task-artifact.fods` existed as a regular 515-byte file. Instrumentation of the guarded reader identified the exact cause: Windows Python reports different `st_ctime_ns` values from `Path.lstat()` and `os.fstat()` for the same file. In five repeated reads of the retained artifact, device, inode, size, and mtime matched, while ctime differed; `st_birthtime_ns` matched across both APIs. The old `_identity()` therefore rejected the same file before reading.

`runtime/guarded_x11_v1/calc_effect_v1.py` now uses `st_birthtime_ns` for the stable file identity when the platform exposes it, and retains the existing ctime fallback elsewhere. Content changes remain checked through file identity, size, mtime, and before/after descriptor comparisons. A regression test writes a blank file and then replaces its contents before `_read_regular()` reads it.

## Verification

All commands ran on current main's source tree (tree `d13ba125ad69921f0a9859fe42e63baf4119ba32`) plus this two-file patch.

- Windows / Python 3.13: `runtime.guarded_x11_v1.test_calc_effect_v1` and `test_calc_task_artifact_v1`: 23/23 PASS, normal and `-O`.
- Windows / Python 3.13: `test_mcp_endpoint_composition.ProviderToPublicMcpCompositionTests.test_fake_app_server_generation_is_recorded_through_calc_profile_and_score`: PASS, normal and `-O`. This was the previously failing composed path.
- Docker Engine 29.8.1, fixed image `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`, Linux/amd64, network disabled, source bind read-only, 2 CPUs, 4 GiB memory/swap, 256 PIDs: the same 23-test suites pass normal and `-O`; the composed test passes normal and `-O`; container exit 0.
- `git diff --check`: PASS.

The committed packet retains the pre-fix diagnostic, an instrumented pre-fix artifact snapshot, five path/descriptor stat comparisons, and Docker output. Full Windows console streams are preserved in the local workspace as `diagnostic-test-output.txt` and `windows-integrated-opt-output.txt`; they are not committed because asyncio debug formatting adds trailing spaces. `SHA256SUMS.txt` covers the committed diagnostic artifacts.

## Scope

This is a Windows file-identity compatibility repair and an offline composition regression. The provider and Calc owner are fakes; no model tokens, live GUI input, WSLc allocation, or task-economics data were collected. It does not establish the Issue #57 integrated live comparison, MAP01, or broad reliability. No consumed live allocation was rerun.
