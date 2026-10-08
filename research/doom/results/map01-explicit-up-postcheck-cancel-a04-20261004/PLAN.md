# A01 frozen construction probe: cancellation before explicit key-up side effect

## H — Hypothesis

For the exact opt-in `input_owner_v12` + `input_transition_owner_v4` composition at frozen merge tree `71b723028a2db51a7f14a6db653d7f3789fa988b`, a queued explicit `up` may be dequeued after the owner loop's cancellation poll returns false. If cancellation becomes set after that poll but before `XTest KeyRelease`, the caller wrapper may still return `ordinary_release_candidate=true` and `owner_thread_keyup_verified=true` without a cancellation-at-key-release field.

This asks about telemetry and event ordering, not whether a release is safe or whether X11/game input was physically consumed.

## T — One deterministic schedule

Use the frozen source snapshot and a fake Xlib boundary. Admit `down(w)`, then request `up(w)`. Intercept the owner's blocking queue read after it removes the `up` request; set the lease cancellation event before returning the request to the owner loop. The fake XTest boundary records the cancellation state at `KeyRelease`. Invoke the candidate once. Preserve result/raw records; do not rerun the candidate.

Container preflight: OrbStack was selected, but `docker image ls --digests` failed before any candidate execution because the daemon reported `operation not supported` while opening a content blob. This is an infrastructure STOP, not a candidate result. The one deterministic host-side code-order probe proceeds because the decision property is the frozen Python queue/branch ordering; it does not qualify container portability.

## D — Decision rule

- `REPRODUCED`: cancellation is set before fake `KeyRelease`, the exact owner-thread sample immediately preceding the dequeued up is false, and the returned transition remains `ordinary_release_candidate=true` with a verified owner receipt.
- `NOT_REPRODUCED`: all gate facts are captured, but one or more of those conditions is false.
- `STOP`: the frozen source cannot run or required order/receipt facts cannot be recorded. Preserve the first STOP; no retry.

## C — Competing interpretation

`ordinary_release_candidate` may intentionally describe lease state at the caller's request time, not cancellation state at the OS-side-effect time. A reproduced schedule therefore establishes an observation-boundary gap in telemetry, not by itself an input-safety defect.

## U — Limits

One forced fake-Xlib interleaving on macOS Python; no frequency estimate, native X server, Windows/WSLc execution, game, GUI, physical key release, application effect, model, useful feedback, or recovery. `XSync`-style receipt semantics remain weaker than target-application consumption.

## Frozen source identity

The candidate snapshot comes from PR #7449 head `a6da76741c91d8cfa0f035445c1fd6b8b864560e` composed with PR #7441 head `5bd1cf7e38e1716e92ab76253d50b48a2385b7f4` and `main` `0db425b379f9438bf6b13c95dce1b763750b06d5`, merge tree `71b723028a2db51a7f14a6db653d7f3789fa988b`.
