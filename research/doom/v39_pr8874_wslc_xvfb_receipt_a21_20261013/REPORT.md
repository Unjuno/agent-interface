# Current-main V4/V12 explicit-up receipt composition A21

## Result

`FAIL_ANALYZER_BRIDGE`. One lowercase `w` traveled through the exact owner implementation frozen from current main by A09 (V4Å®V3Å®V12) on a private Xvfb server. The independent Xlib client observed matching KeyPress/KeyRelease (keycode 25, window 2097152); XQueryKeymap was down while held and up after explicit release. The owner returned exactly one identity-bound explicit KeyRelease/XSync receipt; its nested keymap record verifies the X-server key was up. Close produced a verified empty key/button state, the owner stopped with no live thread, Xvfb exited 0, and the WSLc container was removed.

The unchanged analyzer rejected the exact, unmodified admission and release objects: `measurement_ready=false`, `hold_count=0`, `malformed_admission_count=1`, `invalid_release_count=1`. The admission has `intent_token`, key, keycode and timestamps but no top-level `owner_id`. The V4 single-`up` response has `owner_thread_keyup_verified=true` and a valid nested owner receipt, but leaves `owner_transition_verified=null`; the analyzer requires that field to be true. Independent recomputation over the saved objects exactly matches the candidate analyzer result.

This gives two concrete composition gaps for this direct owner-return stream: the admission is not owner-bound at top level, and the V4 single-up branch does not set the analyzer's transition-verification field even when its stronger nested receipt passes. A production telemetry adapter may enrich or transform these objects; this experiment did not exercise that adapter, so it does not establish a production-path defect. Do not repair the trace by auditor-side inference.

## Measurement and scope

The release caller bracket was 252955 ns (0.252955 ms); V4's nested owner key-release, XSync and server-keymap sample all fall inside it. This is a call bracket, not application-consumption latency.

WSLc 3.0.1.0, Python 3.14.8 linux/amd64, immutable image `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592`, one CPU, no network, source read-only, separate output, UID 65534, `--rm`. Host reported swap/cgroup limits unsupported; no hard memory cap is claimed.

This was one synthetic XTEST key on Xvfb. No physical keyboard, desktop application, Doom/MAP01, useful task effect, model, threat, recovery efficacy, or live allocation was involved. It neither resolves Issue #59 nor validates live computer control. A09's close-only pass and this explicit-up composition answer different questions.

## Evidence

Preregistration and frozen source hashes are in `PREREGISTRATION.md` and `SOURCE_MANIFEST.json`. Raw: `results/a21-01/raw.json` (SHA-256 `44ad7667373b88f6d04d6ef34c72fb44396a2f2c17b96499065318429a1d2305`). Independent audit: `results/a21-01/audit.json`; audit code: `audit.py`. Candidate and complete command output are preserved in `results/a21-01/`.
