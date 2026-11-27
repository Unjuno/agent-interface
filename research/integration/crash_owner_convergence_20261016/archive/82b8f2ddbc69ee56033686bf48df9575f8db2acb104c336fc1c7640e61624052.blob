# A36: XI2 Raw source IDs versus XTest client identity

**H** — XI2 Raw events expose the source device ID for XTest-generated key events, but do not identify which X client connection issued each XTestFakeInput request.

**T** — Private TCP-disabled Xvfb with valid MIT-MAGIC-COOKIE auth and an independent XI2 Raw observer selecting RawKeyPress/RawKeyRelease on the root for AllMasterDevices. The actual process-owned V4 service presses key `a`; a separate Xlib/XTest connection then requests same-key press while the owner hold remains active; the owner performs verified release. The observer records XI2 version, device inventory, and per-phase Raw `deviceid`/`sourceid`, while query_keymap and the core focus-window connection independently observe state/events. No physical device, game, model, or shared X server.

**D** — `PASS_METHOD_SCOPED` if Raw press events arrive in both owner and external phases, owner Raw release arrives, and both press phases have the same `sourceid`; this supports that XI2 identifies the common XTest source device but not the client connection. `FAIL_METHOD_SCOPED` if both phases have raw events with different source IDs, showing source-device distinction in this tested path. `STOP` if XI2 is unavailable, the raw event payload cannot be decoded, or a required phase event is missing.

**C** — XTest-generated input is not physical keyboard input. An XI2 source ID identifies a server device, not a client process or requestor; even a distinct source ID would not prove physical-device attribution.

**U** — No conclusion about physical input/XTest interaction, game delivery, application semantics, or user desktop safety. A result can only refine the source-attribution mechanism for Xvfb/core-XTest.

One frozen candidate invocation; no retries. Allocation: `V39-XI2-XTEST-CLIENT-SOURCE-A36-20261012-01`. A35 established only core-X11 global keymap behavior; A36 tests whether XI2 Raw improves device-source evidence.
