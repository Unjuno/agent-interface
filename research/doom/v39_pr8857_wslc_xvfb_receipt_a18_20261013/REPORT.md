# PR #8857 actual-Xvfb receipt bridge A18

## Result

`FAIL_ANALYZER_BRIDGE` with an independently audited raw result. The WSLc candidate successfully generated and released one lowercase `w` on a private Xvfb server through the exact PR #8857 `InputTransitionOwner v3` wrapper over its unmodified `InputOwner v10` dependency. A separate Xlib client received one matching KeyPress/KeyRelease pair (keycode 25, window 2097152); an independent XQueryKeymap read was `down` while held and `up` after explicit release. Owner close then reported verified empty key/button state, the owner stopped, Xvfb exited 0, and the disposable WSLc container was absent afterward.

The PR analyzer rejected the same actual receipt stream: `measurement_ready=false`, `hold_count=0`, `malformed_admission_count=1`, `invalid_release_count=1`. This is a concrete bridge gap between the PR's fake-owner integration test and the real V10 owner path. The top-level `input_admission` returned by V10 has no `owner_id`; the wrapper only attaches the ID to its private admission marker/embedded release receipt. Further, a successful explicit `up` returns no owner-level verification receipt, so the transition's `owner_transition_verified` is `null`. The analyzer requires both a valid owner-bound admission and `owner_transition_verified is True`.

The outcome does **not** say that the Xvfb key failed to release: both event and server-keymap observers saw release. It says this receipt path cannot yet represent that real owner interaction as a complete verified measurement. The independent auditor rederived the analyzer rejection from raw fields and verified every source SHA/Git blob against PR head `4536ebff7d71848dc86fbf1cdc4f54957eb9ce2d`.

## Measurement

The V10 `down` receipt and V3 caller bracket give a conservative call-bracket interval for the hold:

- Lower bound: `release_call_started_ns - input_ack_ns` = 233,664 ns = **0.233664 ms**.
- Upper bound: `release_call_returned_ns - admitted_ns` = 463,920 ns = **0.463920 ms**.
- Bracket width: **0.230256 ms**.

These are bounds from owner-call timestamps, not a direct timestamp of the X server's physical key transition. The X server/client event pair and keymap samples independently establish the virtual X11 state transition for this one test.

## A17 construction stop

A17's first candidate invocation was retained as `STOP_HARNESS_EVENT_FIELD`. It admitted `w`, then the candidate raised while reading `event.id` from a Python-Xlib event before it could observe the event or invoke explicit up. Its raw and audit are preserved separately; A17 was not rerun. A18 is a new construction ID with the event field access fixed and cleanup state captured in `finally`. A preliminary introspection command also failed because Python-Xlib's `KeyPress._fields` is a `Struct`, not an iterable; it was a tooling probe and did not invoke input.

## Conditions and scope

WSL 3.0.1.0 / WSLc 3.0.1.0, Python 3.14.8 linux/amd64, immutable cached image ID `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592`, `--pull never --network none --cpus 1 --memory 512M --user 65534:65534`, read-only source, separate writable output, and `--rm`. The host reported unsupported swap limits; `--memory` is a request, not an established hard cap. Xvfb printed a nonfatal `/tmp/.X11-unix` ownership warning; its exit code was 0.

Scope is one synthetic XTEST key on private Xvfb. There was no physical keyboard, real desktop app, Doom/MAP01, model call, threat exposure, useful feedback, recovery outcome, or live allocation. This does not close Issue #59.

## Reproduction and retained records

The frozen source and command are in `PREREGISTRATION.md`, `RUN.json`, and `SOURCE_MANIFEST.json`. One candidate run and its combined output are under `results/a18-01/`; the independent result is `results/a18-01/audit.json`. A17's STOP records are under `research/doom/v39_pr8857_wslc_xvfb_receipt_a17_20261013/`.

Next engineering question: before using this analyzer in a production measurement path, make the top-level admission owner-bound and connect `owner_transition_verified` only to a receipt from the actual selected per-key release verifier. Do not set the verification flag from this external Xvfb auditor or infer it from call success. Then validate a supported current-main owner path under a fresh construction ID; live game work still requires the Issue #59 allocation boundary.
