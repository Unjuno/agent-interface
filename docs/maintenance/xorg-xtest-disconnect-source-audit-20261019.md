# X.Org XTEST disconnect/source audit — 2026-10-19

## Question

Does an exact-owner XRes disconnect observation order a delayed XTEST request
from that owner before a separate cleanup connection releases input? The
existing standard-caller Fake X test correctly refuses to promote a mocked
disconnect and empty cleanup readback while an old-client `KeyPress` can still
arrive. This audit checks whether the same post-disconnect schedule is supported
by the X.Org server implementation for its client-owned delayed XTEST path.

## Source trace

The new raw packet for [run 39171499003](https://github.com/Unjuno/agent-interface/actions/runs/39171499003)
records Xvfb at `/usr/bin/Xvfb`, binary SHA-256
`6b27845931670c8c9b3ce7423696a452ce3cab1c7f316ce5f7ea7f1297fa2f84`, installed
package `xvfb=2:21.1.12-1ubuntu1.8`, and X server vendor-release number
`12101011`. The binary package maps to Ubuntu source package
`xorg-server=2:21.1.12-1ubuntu1.8`. The source-package notice publishes SHA-256
`5371522bd81cae405e5300957eb82ced84dea277eb5b7d8eba94e72176d37244` for the
Ubuntu patch; its `configure.ac` and `meson.build` patches set the upstream
version text to `21.1.11`, explaining the raw release number. The source
package's 21.1.12 orig tarball SHA-256 is
`f76a5878b0e6d16415cf0cd24ffc21090845fef3bc4ada45e57ea86b6c8fb75b`, and its
`.dsc` SHA-256 is
`e31053378207d3363ab1cd65c80edc80daafdfef79586e6f3f4a70a6ad38b34d`. These
hashes were independently checked against the Ubuntu source-package files and
notice. The patch does not touch `Xext/xtest.c`, `Xext/sleepuntil.c`,
`dix/dispatch.c`, or `dix/resource.c`. Between upstream 21.1.11 and 21.1.12,
`xtest.c`, `sleepuntil.c`, and `resource.c` are byte-identical; the only
`dispatch.c` difference is in `ProcEstablishConnection`, outside client
teardown. Thus the audited teardown path is present in the actual package
source despite the version-text difference. See the [Ubuntu package
change notice](https://lists.ubuntu.com/archives/noble-changes/2026-July/057023.html),
[runner image manifest](https://github.com/actions/runner-images/blob/ubuntu24/20261012.334/images/ubuntu/Ubuntu2404-Readme.md#installed-apt-packages),
and [retained run log](https://github.com/Unjuno/agent-interface/actions/runs/39171499003).

1. `ProcXTestFakeInput` handles a timestamped event by calling
   `ClientSleepUntil`, resetting the current request, and returning. The sleep
   helper allocates a server resource using `FakeClientID(client->index)` and
   adds that request to its pending timer list. See [`Xext/xtest.c` at the
   release tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.12/Xext/xtest.c#L330)
   and [`Xext/sleepuntil.c` at the release
   tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.12/Xext/sleepuntil.c#L73).
2. The sleep-resource delete callback removes that request from the pending
   list before freeing it. The normal close path calls `FreeClientResources`
   before dropping the client from the server's client table and freeing the
   client object. See [`SertafiedDelete` at the release
   tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.12/Xext/sleepuntil.c#L132),
   [`CloseDownClient` at the release
   tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.12/dix/dispatch.c#L3479),
   and [`FreeClientResources` at the release
   tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.12/dix/resource.c#L1117).
   `InitClient` sets ordinary client connections to `DestroyAll`; only the
   server's client uses `RetainPermanent` by default. The retained test owner
   helper does not send a close-down-mode request, so this is the applicable
   upstream close path for that test source. An X client that explicitly
   requests retained resources is outside this inference.
3. For a non-delayed XTEST input request, `ProcXTestFakeInput` calls
   `mieqProcessDeviceEvent` before returning. That is a separate synchronous
   request-processing path; it does not show that the physical application
   effect or an OS-level held-input state is independently verified. See
   [`Xext/xtest.c` at the release
   tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.12/Xext/xtest.c#L430)
   and [`mi/mieq.c` at the release
   tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.12/mi/mieq.c#L449).

## Bounded interpretation

For the exact installed Ubuntu source package, the default-close-mode test
owner has its server-side delayed XTEST resource removed during normal
client-resource teardown. This narrows the Fake X late-request schedule for
this specific delayed-XTEST/default-close-mode path. It does not generalize to
clients that request retained resources.

The retained PID-qualified private-Xvfb packet reports X.Org release `12101011`,
an 8-second delayed XTEST request, owner-PID-qualified `disconnected` at about
74.5 ms after owner termination, and keys up after the event horizon. Run
39171499003 independently reproduced this bounded observation with the
identified Ubuntu package; it also did not measure a held key already down
followed by a separate release/readback. Keep the prior packet's scope and
HOLD/UNKNOWN labels unchanged. See the
[retained raw-backed packet](../../research/integration/xorg_xres_disconnect_order_20261019/README.md)
and [standard-caller Fake X counterexample](../../research/integration/standard_caller_release_order_composition_20261019/README.md).

This does **not** establish a bounded physical release under a blocked X server.
If the server cannot process the owner EOF, XRes cannot confirm disconnect and
a cleanup request on that server cannot run. The existing caller's bounded
helper timeout then yields `UNKNOWN`; it does not release the held input. A
server-independent watchdog or input path would be needed to claim release
under that fault. X.Org source behavior also does not transfer to XWayland,
XQuartz, VcXsrv, other server versions, or other input backends without
separate qualification.

## Next discriminator

The Xvfb integration test now adds the executable path/SHA-256 and installed
package versions to its raw report. The provenance helper test passes on
Windows in normal and optimized Python. Run 39171499003 executes the collector
on the private Linux Xvfb and resolves the source/version discrepancy above.
Only with a newly verified unused allocation, test the standard caller
with an already-held key/button, owner termination, PID-qualified disconnect,
independent release connection, sync, and independent post-horizon
keymap/application readback. Keep server-I/O stall as a separate arm: if
disconnect or cleanup misses its bound, require bounded `UNKNOWN` and do not
claim physical release. Do not rerun consumed A11 or reclassify any earlier
result from this source audit.
