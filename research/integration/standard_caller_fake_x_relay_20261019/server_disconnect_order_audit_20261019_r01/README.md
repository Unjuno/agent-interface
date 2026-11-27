# X11 server disconnect ordering audit r01 — 2026-10-19

## Disposition

`SOURCE_AUDIT_SCOPED; LIVE_SERVER_ORDER_UNKNOWN`. This packet refines what the
existing [Fake X late-down counterexample](../late-down-after-release-counterexample-20261019-r01/README.md)
means. It does not alter or replace that result. The test's order—observe owner
disconnect, obtain an empty keymap readback on a fresh connection, then apply a
KeyPress that was queued on the retired connection—is an injected Fake X
schedule. No X server execution has established that this order can occur.

## Source observations

The X11 protocol concurrency chapter requires each server request to complete
in some serial order, preserves delivery order within each connection, and says
the combined order across clients is a shuffle of their individual streams.
This permits cross-client interleaving, but it does not by itself show that a
request from a connection can execute after the server has reported that same
connection disconnected. The X protocol's connection-close section lists
resource, grab, and selection cleanup; it does not specify XTEST key-state
recovery on close. [X11 protocol, §§10 and 12](https://xorg.freedesktop.org/archive/current/doc/xproto/x11protocol.pdf).

The XTEST request has an optional delay. Its specification says the server does
not process other requests from that client until the delay and simulated-event
processing finish. It leaves this packet's key question open: what the server
does if that client disconnects while the delayed request is sleeping or being
resumed. [XTEST protocol, §2](https://www.x.org/releases/X11R7.5/doc/Xext/xtest.pdf).

The X.Org sample-server porting guide states that request bytes are read from
each client's ordered byte stream and complete requests are passed to DIX for
dispatch; it also describes scheduler yields between clients. That is general
server guidance rather than a guarantee for every supported X server or a
version-pinned audit of the host server. [X.Org server porting guide](https://xorg.freedesktop.org/releases/X11R7.7/doc/xorg-server/Xserver-spec.html).

As a version-specific implementation illustration only, the XQuartz xorg-server
source currently dispatches `XTestFakeInput` through `GetKeyboardEvents` and
`mieqProcessDeviceEvent`, whose normal path calls the device input procedure;
its DIX loop checks pending input between request reads. XQuartz is a fork and
this is not evidence for the Linux server used by the target caller.
[XQuartz XTEST handler](https://github.com/XQuartz/xorg-server/blob/master/Xext/xtest.c),
[event processing](https://github.com/XQuartz/xorg-server/blob/master/mi/mieq.c),
[DIX dispatch loop](https://github.com/XQuartz/xorg-server/blob/master/dix/dispatch.c).

## What this changes

The existing late-down test remains a valid caller-policy check: given an
uncertain late press after a purported release readback, the caller keeps
cleanup `UNKNOWN`, denies replay, and withholds task success. It is not a
server-order counterexample. Do not infer either that the schedule is possible
or that XRes disconnection is a sufficient input fence from these sources
alone.

The next server experiment should distinguish ordinary complete requests from
the deferred XTEST case, on a private isolated Xvfb instance with no desktop or
application input:

1. Record the exact Xvfb/X.Org build, XTEST and XRes versions, transport, one
   owner PID/resource-base pair, request sequence, and server-side event order.
2. Use an observer connection to check XRes presence and `XQueryKeymap`. Run a
   healthy delayed-press control, then terminate an owner while a delayed
   `XTestFakeInput(KeyPress)` is outstanding. Observe whether the server reports
   disconnect before or after processing the event.
3. Once disconnect is observed, issue a release on the observer connection,
   synchronize, verify an empty keymap, then observe beyond the maximum
   configured XTEST delay. A later KeyPress invalidates the proposed fence;
   a clean run is only scoped evidence for that server/version and request path.
4. Separately exercise synchronous blocked I/O after a completed KeyPress. Keep
   its caller-return bound, server key-state readback, and any late event as
   separate measurements. The delayed-XTEST case alone is not a blocked-I/O
   result.

Retain the first failure and raw protocol/event trace. Do not replay the
existing formal A02/A03 inputs or use a shared desktop. A successful server
ordering test would still not prove physical hardware release, application
effect, bounded recovery, task success, MAP01 completion, or efficiency.

## Current environment gate

This audit ran no X server, XTEST request, GUI input, WSLc command, container,
game, model, or formal allocation. A read-only Windows process/path check found
no local Xvfb/Xorg/VcXsrv executable or running X server, while a
`wslcsession.exe` process is active; WSLc ownership and unused allocation are
not verified. Therefore the server experiment remains unrun and the overall
release gate remains open.
