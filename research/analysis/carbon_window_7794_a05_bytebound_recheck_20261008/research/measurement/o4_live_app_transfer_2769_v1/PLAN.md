# Issue #2769 — live X11 pixel VERIFY transfer v1

Base: `5337efa0394d2c0e4a6d5cb8010f177caf042681`
Branch: `research/o4-live-app-transfer-2769-20260922-v1`
Path: `research/measurement/o4_live_app_transfer_2769_v1/**`

## H
A pixel VERIFY gate that resolves locally only when a live-generated effect signature is bound to the same current application window/generation can preserve TRUE/FALSE on current evidence while stale, timeout, replacement, malformed, and delayed-return evidence escalates. A lineage-blind pixel comparator will resolve some invalid evidence unsafely.

## T
Two installed X11 applications (`xterm`, `xmessage`) × nine classes = 18 fresh private-Xvfb sessions. Classes: current_false, current_true, stale_after_newer, timeout_before, timeout_after, replacement, visual_similar_non_effect, malformed, delayed_verifier. No XTEST/input/model/provider/network. Application-side state/effect journals are generated independently of candidate verdicts. Live EFFECT signatures are captured from the application, never authored as RGB constants. Construction: four excluded rows. Formal: one 18-row invocation, no retry/replacement/tuning.

## D
PASS_O4_X11_PIXEL_VERIFY_LIVE_TRANSFER_SCOPED iff all 18 rows exist, candidate/oracle mismatch=0, unsafe candidate local resolutions=0 for invalid classes, current TRUE/FALSE classify correctly in both apps, independent raw audit errors=0, >=8 semantic corruption controls reject, all app/Xvfb processes terminate, source hashes remain frozen. Missing source/process/raw evidence => HOLD/STOP. Contrary complete semantic result => FAIL.

## C
xmessage changes are process/window replacements; xterm changes occur through fresh application processes in this first rung, with request/capture/return window and generation identity checked explicitly. Both are simple X11 clients. Effect truth is an application-side declared state transition in the private harness, not a user task. XGetImage bytes are server-side pixels, not model-visible tokens.

## U
No arbitrary-app generality, model utility, token/end-to-end latency benefit, input authority, cross-platform, or production claim. Same-author audit is not external review. Natural timeout/race rates are not estimated.
