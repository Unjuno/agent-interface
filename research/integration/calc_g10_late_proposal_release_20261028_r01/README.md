# G10 late proposal and release composition check

- Date: 2026-10-28 (Asia/Tokyo)
- Repository base: `3363a3fa37ef33360d0fda5a62c3bb3f11fee7d5`
- Branch: `research/calc-delay-proposal-release-20261028`

## Question and change

Can a proposal worker started before its finite deadline return after timeout and cause another input, or can snapshot copying start a worker after cancellation/deadline expiry?

`calc_bounded_proposal_v1.py` now rechecks cancellation and deadline after copying the native observation and image, before starting the worker. The regression coverage checks cancellation and deadline expiry during copying. The caller-level Fake X case blocks the second-target proposal past a 30 ms timeout, observes the retained first transition and its verified empty release, then releases the late callback and confirms it still cannot mint or dispatch a second target or invoke outer task scoring.

## Conditions and results

- Windows NT 10.0.26300.0, CPython 3.11.9. Tests ran from the isolated checkout at the base SHA with the change on the branch above.
- The changed composition test and proposal worker were imported from that checkout. The `NativeHandleBridge`, X11 runtime session, guarded adapter, compiled core and caller used repository implementations. `import-paths.txt` records the resolved module paths.
- Supporting unchanged research modules were loaded from `D:\CodexData\Temp\agent-interface-currentmain-calc-g10-delay-release-r01-20261028`; their base blob IDs are in `SOURCE_BASE_BLOBS.txt` and match the source manifest from the already audited current-main packet.
- The test uses the retained G10 interface bytes (`raw.json`, SHA-256 `890c68f13e5fa8598bcbb2f456b8ee5319c584249c19492744a7c96f170014bf`). Transport and application pixels are Fake X. No Calc, OCR, model/provider, real X server, Docker, WSLc or live allocation was used.
- Normal: 10/10 passed, exit 0. Optimized (`-O`): 10/10 passed, exit 0. Logs are retained in `normal.log` and `optimized.log`.
- The late-callback test terminates `EXECUTION_INCOMPLETE` with one completed transition; the first execution has a verified empty key/button release, and there is no second input, reference mint or outer score. The timed-out Python worker remains alive until the test releases it. This verifies that its late result is ignored; it does not prove that a callback with arbitrary side effects can be sandboxed or forcibly terminated.

Exact test commands (run from the repository root with the recorded support-source fixture on `PYTHONPATH`):

```text
python -B -m unittest research.live_control.test_calc_bounded_proposal_v1 research.integration.test_calc_g10_native_caller_composition_v1
python -B -O -m unittest research.live_control.test_calc_bounded_proposal_v1 research.integration.test_calc_g10_native_caller_composition_v1
```

## Setup failure retained

The first scratch-copy invocation omitted the retained `raw.json` fixture and failed three integration cases before any Fake X action. The missing file was restored byte-for-byte from the base commit and its SHA-256 verified before both passing runs. See `attempt-01-setup-missing-raw.txt`. This was an evidence-packaging error, not an application or recovery result.
