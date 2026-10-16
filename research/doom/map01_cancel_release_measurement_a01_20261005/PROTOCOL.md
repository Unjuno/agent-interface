# MAP01 cancellation cleanup per-key receipt A01

## H — hypothesis

When a v39 per-key bridge admits a physical key-down and the lease is cancelled asynchronously, InputOwner's verified internal cleanup releases the physical key but does not emit a bridge-visible per-key up/release measurement joined to that admitted hold.

## T — test

Use the frozen current-main v12 InputOwner, v39 bridge, and their existing fake-display harness. Through the bridge, admit one F8 down under a program/step context; set the lease cancellation event; wait up to 1 second for the owner's `reason=cancelled` release record; capture the fake physical key state, owner records, and bridge event stream. No X server, GUI, game, or OS input is used.

## D — decision

`PASS_GAP_CONFIRMED` if exactly one admission is observed with a physical actuation ID and program/step context, fake physical state is empty after cancellation, a verified cancellation owner-release record exists, and no bridge-visible matching per-key up event exists. `FAIL_HYPOTHESIS` if a matching up receipt is emitted or physical release is not verified despite complete execution. Import failure, missing release record, or timeout is `HOLD_CONSTRUCTION`. Execute once; preserve the first outcome without repair or rerun.

## C — competing explanations

Aggregate verified-empty cleanup may be an intentional boundary that prevents fabricating a per-key edge. The test only checks what the current fake owner and bridge emit; it does not challenge whether XTest plus keymap sampling matches another application or hardware keyboard.

## U — limits

This is one deterministic fake-display cancellation path. It estimates no physical release latency, real X11/server behavior, application consumption, useful feedback, recovery effectiveness, gameplay, MAP01 success, or safety. It grants no live allocation.
