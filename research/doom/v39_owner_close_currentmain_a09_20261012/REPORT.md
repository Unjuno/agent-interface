# A09 result — current-main V39 owner close on isolated Xvfb

**Decision: `PASS_METHOD_SCOPED`.** One key admission from exact current main `f185a9059d485a4f8d5a65e9e7f6782897f67eae` was closed through the V4→V3→V12 owner on TCP-disabled Xvfb display `:131`. The same focused client window observed a matching KeyPress then KeyRelease for keycode 38 (`a`). The independent observer keymap reported the key up. V12 recorded exactly one `owner_release(reason=close)` with the same `intent_token`, verified true, empty keys/buttons/unknown state, and a matching per-key receipt whose first and only attempt sampled the key down before release and up afterward. The owner closed/stopped with no live thread; Xvfb exited 0.

The candidate ran once and exited 0. The independent raw-only auditor ran once and passed all ten checks. The retained raw is `results/A09/RAW.json` (SHA-256 `8b0ee889c50ad2bb69470bf1faf0e55ff21b81660c72dc3e68dd17e25608eb69`); the audit is `results/A09/AUDIT.json` (SHA-256 `ab6d7121a909c55362cdb1de76373a9428297af1afc86f4b25005ead50580405`). The candidate source is `SOURCE/candidate.py` (SHA-256 `267b42af54b2aa09bb1cbbe7928bb9978ea81fb929f272bf3d34ea4085fd41f1`); the auditor is `SOURCE/audit.py` (SHA-256 `9d0c01f429ea30729540d55517b3482b7ea2e8f6ca424f7ec6e79da2312d65b1`). The current-main focused regression set also passed: 11/11 tests.

## Why this is a distinct current-main check

A08 established the same close-path behavior against an earlier owner snapshot. Current main now has different V12 and V3 source bytes: V12 includes the accepted `keycode` and owner-release `intent_token` fields; V3 has additional cancellation-cleanup reconciliation. A09 froze the exact current-main V10/V12/V3/V4 files and tested the updated composition. It does not rerun or overwrite A07/A08.

Frozen source SHA-256 values are in `FREEZE.json`. The test image was built from cached `python@sha256:b9767f56a1cc620aa72d38cc3557d26412e38a4597c92953476136b78894ccbd`; the resulting WSLc image ID was `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592`. It contained Python 3.14.8, Python-Xlib 0.33, Xvfb and xserver-common `2:21.1.16-1.3+deb13u4`. Package installation used network during image build only. Candidate and audit containers used `--pull never --network none`, one requested CPU, a read-only package mount, a separate writable results mount, and `--rm`. WSLc reported that cgroup/swap-limit support is unavailable; the requested memory value is not evidence of a hard cap.

The first disposable environment metadata probe stopped because its shell query used unsupported parameter substitution. That probe did not invoke the candidate. A separate environment-only check then passed before freeze finalization; both outputs are preserved under `RUNNER/`.

## Scope and remaining uncertainty

This is one synthetic X-server path. It strengthens the current-main input-owner close evidence but does not establish physical keyboard state, delivery to a real desktop or game, repeated reliability, response latency under load, useful task feedback, MAP01 progress, bounded recovery, or task success. Issue #59 remains unresolved and still needs a separately assigned live MAP01 allocation for those endpoints. This result does not consume or authorize one.

Exact commands and runner logs are in `COMMANDS.txt` and `RUNNER/`. The result leaf is one-shot and must not be rerun or overwritten.
