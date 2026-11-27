# R31: current-main supervisor source transplant

Date: 2026-10-22

## Question

Do the PR #9315 runtime source and the six local follow-up source/test changes
apply to the then-current `main` base and pass the focused regression scope?

## Conditions

- Base: `e7c1c41dcf0f552fb85154d6905bd0820591ea81` (fetched `origin/main`).
- PR source: exact PR head `76626da8b03df25024d12efb5f1dde2f12c53ed2`.
- Applied only the eight runtime paths from that PR. The six locally modified
  runtime/test files were then copied from the existing supervisor worktree;
  no docs or experiment packet was imported into this validation tree.
- Platform: Windows, Python 3.11.9, repository Fake X fixtures. No WSL,
  WSLc, Xvfb server, physical desktop, or provider was used.
- Focused modules: `runtime.cli_v1.test_mcp_owned_process`,
  `runtime.cli_v1.test_mcp_guarded`,
  `runtime.guarded_x11_v1.test_cancel_supervisor`, and
  `runtime.guarded_x11_v1.test_xres_client_fence`.

## Results

- Normal Python: **116/116 passed**, exit 0 (`normal.raw.log`).
- Optimized Python (`-O`): **116/116 passed**, exit 0
  (`optimized.raw.log`).
- Xvfb-only modules: **4 passed, 2 skipped** on Windows. The two skipped
  cases require the Linux Xvfb environment; this run gives no live-X evidence.
- The seven source files fingerprinted before and after both focused runs are
  byte-identical (`source-before.json`, `source-after.json`).
- `git diff --check` passed on the validation worktree.

The result establishes focused Fake X compatibility of this source slice on
the fetched main base. It does not establish live-X release under blocked I/O,
reliability, WSLc portability, MAP01, provider effect, or efficiency. It does
not itself update PR #9315 or change any remote ref.

## Reproduction

From repository root:

```powershell
python -m unittest runtime.cli_v1.test_mcp_owned_process runtime.cli_v1.test_mcp_guarded runtime.guarded_x11_v1.test_cancel_supervisor runtime.guarded_x11_v1.test_xres_client_fence
python -O -m unittest runtime.cli_v1.test_mcp_owned_process runtime.cli_v1.test_mcp_guarded runtime.guarded_x11_v1.test_cancel_supervisor runtime.guarded_x11_v1.test_xres_client_fence
python -m unittest runtime.cli_v1.test_mcp_xvfb_blocked_release_integration runtime.cli_v1.test_mcp_xvfb_server_stop_integration
```

The test output, exit codes, conditions, and source hashes are preserved in
this packet. `SHA256SUMS` covers every packet file except itself.
