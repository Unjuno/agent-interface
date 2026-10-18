# A03 — alias refusal followed by owner-close cleanup

## Result

Follow-up to the documented gap in [PR #8250](https://github.com/Unjuno/agent-interface/pull/8250): that PR explicitly leaves caller exception-to-cleanup behavior untested. This A03 tests an explicit owner close after refusal, but still does not execute the complete V15/V39 caller unwind.



**Scoped disposition: `PASS_METHOD_SCOPED_AUDIT_V2`.** One private Xvfb case exercised the candidate-only two-line duplicate-resolved-keycode guard through the actual V4→V3→V12 InputOwner composition. Xvfb resolved both `a` and `A` to keycode 38. The owner admitted and held `a`; `up_batch(["a", "A"])` raised `ValueError: distinct resolved keycodes required for up_batch`. No key event was emitted by the refusal, and the server keymap still showed the key down.

The test then called the actual V4 owner wrapper's `close()`. Xvfb delivered the matching KeyRelease to the same window that received KeyPress. The final V12 `owner_release` record reports `reason=close`, `verified=true`, `keys_down=[]`, `keys_unknown=[]`; the observer keymap was neutral, the owner thread had stopped, and Xvfb exited 0.

The candidate raw is `results/A03_RAW.json` (SHA-256 `b16fb6f5f572f1e1e6a7a98a080e9cb8b0ef619d60fe76c0f02720dca64ba6b8`). It was run exactly once. No candidate rerun occurred.

## Audit history

The originally frozen raw-only auditor v1 is preserved as `results/A03_AUDIT.json` and reports `FAIL` on one check because the candidate did not include a redundant `client_window` field. It did not find a release/keymap/receipt contradiction: 10/11 checks passed. That failure remains unchanged.

A separately frozen read-only auditor v2 binds the release event's window to the recorded press event's window and verifies that its observed timestamp follows the terminal verified-release receipt. It audits the same saved raw, without rerunning the candidate, and passes 11/11 checks. Its freeze, source, result, and hashes are `A03_AUDIT_V2_FREEZE.json`, `audit_v2.py`, and `results/A03_AUDIT_V2.json` (result SHA-256 `80e6bc6176635392eb4c50939c0eb1f5c62a05a42797ffa08a3b93e87957f358`).

## Provenance and limits

The experiment is frozen against current main `decc1896e3e85ab2fdbb7ec4678f958eb6561d0f`. Baseline V12 Git blob is `d11a9b1328bf76e5045022c581d6a9a721bf9585`; transition-owner V3/V4 blobs are `0a1772d1687d49bd49f048b9d7ba659ed18247a5` and `ac1cc0e67114e2b8630acbaa6d94bf2a73686a55`. Only the test copy has the uniqueness guard. Runtime was the cached image digest in `FREEZE.json`, with network disabled, read-only source/root filesystem, 2 CPU and 4 GiB cgroup limits; preflight observed cpu.max=200000 100000 and memory.max=4294967296. Docker daemon reported 24 host CPUs and 33,562,464,256 bytes host memory. The candidate itself ran one isolated TCP-disabled Xvfb server and no game or GUI application.

This qualifies the V4→V3→V12 owner-close path after a guarded alias refusal. The caller explicitly invoked `close()`. It does not prove that a V15 backend or V39 controller always reaches that close path after an exception, nor does it establish physical keyboard state, application consumption, task effect, useful feedback, recovery benefit, a latency bound, threat exposure, or MAP01 completion. Issue #59's integrated live gate remains open and unassigned.

## Reproduction

The first-outcome and auditor commands, pinned image, resource controls, and output paths are recorded in `FREEZE.json` and `A03_AUDIT_V2_FREEZE.json`. The raw output is retained rather than regenerated. To reproduce only the read-only audit, use the command in `A03_AUDIT_V2_FREEZE.json` against the preserved raw.
