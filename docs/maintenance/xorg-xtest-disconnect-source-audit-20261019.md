# X.Org XTEST disconnect/source audit — 2026-10-19

## Question

Does an exact-owner XRes disconnect observation order a delayed XTEST request
from that owner before a separate cleanup connection releases input? The
existing standard-caller Fake X test correctly refuses to promote a mocked
disconnect and empty cleanup readback while an old-client `KeyPress` can still
arrive. This audit checks whether the same post-disconnect schedule is supported
by the X.Org server implementation for its client-owned delayed XTEST path.

## Source trace

The inspected source is the official X.Org server 21.1.11 release archive,
tagged `xorg-server-21.1.11`. The retained run reports vendor release number
`12101011`. The release's `configure.ac` encodes versions as
`10000000 + major*100000 + minor*1000 + patch`; 21.1.11 maps exactly to
`12101011`. I downloaded the official release archive and independently
verified SHA-256
`1aa0ee1adad0b2db7f291f3823a4ab240c7f4aea710e89f5ef4aa232b6833403`, matching
the release announcement. See the [X.Org release announcement and published
hash](https://www.mail-archive.com/xorg%40lists.x.org/msg07587.html) and the
[official source archive](https://xorg.freedesktop.org/archive/individual/xserver/xorg-server-21.1.11.tar.gz).
This identifies the upstream 21.1.11 source matching the raw's reported
release number; it does not yet identify the CI binary or its package source.
The retained run log identifies GitHub runner image `ubuntu-24.04`, image
release `ubuntu24/20261012.334`, and the workflow's later `apt-get update` /
`apt-get install xvfb`. The image's published software list records Xvfb
package `2:21.1.12-1ubuntu1.8`, which does not match the raw's 21.1.11 vendor
release. Since the install step's selected package version was not retained,
the image manifest cannot establish which binary the test launched; this is a
provenance discrepancy to resolve, not evidence that the run used either
version. See the [runner image manifest](https://github.com/actions/runner-images/blob/ubuntu24/20261012.334/images/ubuntu/Ubuntu2404-Readme.md#installed-apt-packages)
and the retained [run log](https://github.com/Unjuno/agent-interface/actions/runs/39160684353).

1. `ProcXTestFakeInput` handles a timestamped event by calling
   `ClientSleepUntil`, resetting the current request, and returning. The sleep
   helper allocates a server resource using `FakeClientID(client->index)` and
   adds that request to its pending timer list. See [`Xext/xtest.c` at the
   release tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.11/Xext/xtest.c#L330)
   and [`Xext/sleepuntil.c` at the release
   tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.11/Xext/sleepuntil.c#L73).
2. The sleep-resource delete callback removes that request from the pending
   list before freeing it. The normal close path calls `FreeClientResources`
   before dropping the client from the server's client table and freeing the
   client object. See [`SertafiedDelete` at the release
   tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.11/Xext/sleepuntil.c#L132),
   [`CloseDownClient` at the release
   tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.11/dix/dispatch.c#L3479),
   and [`FreeClientResources` at the release
   tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.11/dix/resource.c#L1117).
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
   tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.11/Xext/xtest.c#L430)
   and [`mi/mieq.c` at the release
   tag](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.11/mi/mieq.c#L449).

## Bounded interpretation

For upstream X.Org 21.1.11, the default-close-mode test owner has its
server-side delayed XTEST resource removed during normal client-resource
teardown. This narrows the Fake X late-request schedule for this specific
delayed-XTEST/default-close-mode path. However, because the CI image manifest
and raw vendor release disagree and the post-install package version is
missing, do not transfer this source conclusion to the retained binary yet.
It also does not generalize to clients that request retained resources.

The retained PID-qualified private-Xvfb packet reports X.Org release `12101011`,
an 8-second delayed XTEST request, owner-PID-qualified `disconnected` at about
74.5 ms after owner termination, and keys up after the event horizon. That
observation is consistent with upstream 21.1.11, but the exact CI package/build
identity remains unresolved, and the run did not measure a held key already
down followed by a separate release/readback. Keep the packet's original
scope and HOLD/UNKNOWN labels unchanged. See the
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

The Xvfb integration test now adds the executable path/SHA-256 and
`dpkg-query` versions for `xvfb` and `xserver-xorg-core` to its raw report. Its
helper test passes on Windows in normal and optimized Python; the live private
Xvfb class was skipped there and the new collector has not yet run on Linux.
On the next private-Xvfb run, reconcile raw `12101011` against the captured
binary/package metadata and source patches. After that, only with a newly
verified unused allocation, test the standard caller
with an already-held key/button, owner termination, PID-qualified disconnect,
independent release connection, sync, and independent post-horizon
keymap/application readback. Keep server-I/O stall as a separate arm: if
disconnect or cleanup misses its bound, require bounded `UNKNOWN` and do not
claim physical release. Do not rerun consumed A11 or reclassify any earlier
result from this source audit.
