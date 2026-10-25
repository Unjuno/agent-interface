# Current-main post-#9557 cancellation and generation regression

## Source

- Remote `main` was verified with `git ls-remote` as `a3991e0c07ab847f7fd4da868f319843f3f2adbc`.
- A clean detached worktree was created at that exact SHA. `git status --porcelain` was empty before the test run, and the checkout had no source changes afterward.

## Verification

The following selected local suite passed 77/77 under Python 3.13.14 in normal mode and 77/77 with `-O`:

```text
runtime.cli_v1.test_mcp_owned_process
runtime.guarded_x11_v1.test_cancel_supervisor
runtime.cli_v1.test_target_generation_admission
runtime.cli_v1.test_mcp_win32_composition
```

The Win32 composition tests emitted asyncio slow-task diagnostics, but both test processes exited successfully. `git diff --check` passed. These suites use synthetic/local fixtures; no physical input, GUI, WSLc, or Docker operation occurred.

## Scope

This establishes a clean current-main checkout and local regression baseline after #9557. It clears only the missing-checkout prerequisite recorded in #7924. Shared WSLc client/session ownership remains unknown, so the issue remains STOP/HOLD and no WSLc allocation was used. This does not establish live input release, recovery, task effect, provider accounting, matched efficiency, or reliability.

## #9420 XRes integration CI flake follow-up (2026-10-25)

The failed `x11-integration` job in run `39910203208` exposed a test-harness publication race: `_OWNER_START` and `_HELD_OWNER_START` created the final JSON marker before `json.dump` completed, while the parent treated `marker.exists()` as proof the JSON was complete. The idle-owner helper already used a temporary file and `os.replace`.

Both remaining helpers now write `marker + '.tmp'` and publish it with `os.replace`. `OwnerMarkerPublicationTests` compiles and checks all three embedded helper scripts, then executes the actual `_OWNER_START` source with fake Xlib and pauses its JSON writer. During the pause, the final marker stays absent and the temporary marker exists. On Windows/Python 3.13.14, these focused tests passed 2/2 in normal and optimized mode; the containing integration module passed 3 tests with 2 private-Xorg tests skipped in both modes. A mutation replacing the temporary path with the final path failed at the expected in-write visibility assertion, demonstrating that the regression test detects the prior race. `git diff --check` passed. This is a local harness-level repair only; no live X server was exercised here.

The current-main `runtime.cli_v1.test_mcp_supervised_win32` module also passed 17/17 normally and 17/17 under `-O` on Python 3.13.14. The run emitted one asyncio slow-task diagnostic in the normal mode; both modes exited successfully. These synthetic caller tests do not exercise actual Windows input or the XRes integration server.
