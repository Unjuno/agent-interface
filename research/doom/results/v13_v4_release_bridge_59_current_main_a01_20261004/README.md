# Issue #59: current-main V13-to-V4 release-batch bridge construction A01

Date: 2026-10-04. Frozen source baseline: `dae347cb8333f4469c89b076b0b466cc8bf6b960`.

## H/T/D/C/U

**H — Hypothesis.** Current-main V13/V11 returns an `input_release_rpc` dictionary for ordinary key-up. Current-main V3 still requires the inner owner call to return `None`; it raises before V4 can join the owner-thread key-up receipt. An adapter can retain and validate the V13 receipt while returning `None` across the V3 contract boundary. Missing or mismatched receipt evidence must disqualify ordinary release.

**T — Test.** The frozen test loads byte-exact current-main V3, V4, V11, V13, and release-batch backend sources. A deterministic fake V10 owner records the key-up and returns `None`, isolating the wrapper contract from X11. The suite first reproduces the direct-composition assertion, then checks the bridge, invalid/missing receipt handling, and both the current-main release-batch backend and retained PR #7449 backend source. An independent auditor reads the emitted valid row.

**D — Outcome.** Native Windows construction outcome: `PASS_CONSTRUCTION_SCOPED`. All 5 unittest methods passed; the direct V13-to-V3 composition raised the expected payload assertion, the adapted valid path retained the V4/key-up join, and wrong/missing receipts failed closed. The current-main batch consumer marked the valid joined transition verified and the wrong-token case unverified. The separate saved-row audit passed 18 checks. **Environment qualification remains `UNQUALIFIED_WSLc_UNAVAILABLE`:** repository instructions call for WSLc for eligible local CPU construction, but `C:\Program Files\WSL\wslc.exe` is absent. The native result is retained as a bounded diagnostic and is not claimed as WSLc-qualified Issue evidence.

**C — Competing explanation.** The fake base owner and state sample may hide scheduling or import-graph behavior. The adapter is a candidate only; this result does not establish thread-safe concurrency, packaged-session compatibility, or adoption.

**U — Uncertainty.** No X server, XTest event, physical transition, application effect, game, model, fresh scorer, matched recovery condition, or live allocation was used. The saved row contains synthetic owner receipts. No input authority is granted.

## Post-run source composition limit

The read-only follow-up in [`SOURCE-COMPOSITION-LIMITATION.md`](SOURCE-COMPOSITION-LIMITATION.md) compares A01 with the later main package from PR #7542. That package composes its frozen V12 cancellation-interval source with Executor V13/V4 tests, but does not include the current `input_owner_v13.py` and makes no runtime-source edit. A01 complements it by testing ordinary V13 explicit-up receipts through V3/V4 and the current batch consumer. Neither result establishes one integrated source graph that retains both ordinary V13 receipts and V12 cancellation intervals.

## Exact sources

The source copies and SHA-256/Git-blob pins are in `FREEZE.json`; `preflight_current_source.py` verified all 10 Python source files and all 6 exact Git blobs before the run. The primary stack uses current-main V13/V11/V3/V4 plus the current-main batch backend. The additional PR #7449 backend is an explicitly pinned historical comparator, not current main. The candidate adapter and test harness are not runtime-adopted.

## Evidence and reproduction

`runs/a01/` retains the preflight, raw unittest output, synthetic trace, independent audit output, and run result. On native Windows with CPython 3.13.14, from `source/`:

```powershell
py -3.13 preflight_current_source.py ../FREEZE.json
$env:BRIDGE_TRACE_OUTPUT = '..\runs\a01\trace.json'
py -3.13 -m unittest -v test_transition_v4_rpc_bridge
Remove-Item Env:\BRIDGE_TRACE_OUTPUT
py -3.13 audit_v13_v4_backend_bridge.py ..\runs\a01\trace.json
```

The earlier `v13_v4_release_bridge_59_construction_v1/` package is preserved as a pre-#7513 source snapshot. This A01 uses the integrated current-main source after #7513/#7515 and supersedes it for current-source analysis; neither package establishes runtime or physical-input qualification.
