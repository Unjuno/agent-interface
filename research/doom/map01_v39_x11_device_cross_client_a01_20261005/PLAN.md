# XTEST device-event cross-client experiment — A01

Issue: [#59](https://github.com/Unjuno/agent-interface/issues/59); related current cleanup PR: [#7910](https://github.com/Unjuno/agent-interface/pull/7910).

## H / T / D / C / U

- **H:** Calling `XTestFakeDeviceKeyEvent` through two independent X client connections that open the same server-provided XTEST virtual keyboard preserves the core key while client B remains logically down after client A sends UP. This would distinguish device-specific XTEST from the shared-core behavior implicated by #59.
- **T:** One frozen candidate run on a fresh private Xvfb, first using the `XTestFakeKeyEvent` control, then `XTestFakeDeviceKeyEvent`. For each route, client A sends W-DOWN, client B sends W-DOWN, A sends W-UP while B has not sent UP, then B sends W-UP. An independent connection samples `XQueryKeymap`; a focused core Xlib client records every W KeyPress/KeyRelease and target window. Run a separate saved-raw auditor once after candidate exit 0.
- **D:** The core control must show W down after each DOWN and a matching core KeyRelease/neutral keymap immediately after A-UP while B's logical hold is outstanding; otherwise STOP. The device-specific path supports isolation only if its key remains down and it withholds the core KeyRelease until B-UP. If it releases at A-UP, FAIL the isolation hypothesis. Candidate once, no retry.
- **C:** One Xvfb build and the server's shared XTEST virtual keyboard are tested. XTEST may treat repeated DOWNs or UPs as server-level transitions; the test measures core-client-visible behavior, not application-specific semantics.
- **U:** No production GUI/game, model, physical input, task feedback, safety claim, or live allocation. A positive result would still need proof with separately provisioned devices and an actual application; a negative result rules out only this shared XTEST-device route.

## Frozen sources and run boundaries

The Xvfb/X server and xkbcomp are extracted from the pinned Ubuntu .deb files retained by the earlier setup STOP, not installed into the distro. The new output path has its own package copies, hashes, candidate, auditor, raw result and command receipts. Server socket isolation uses a private mount namespace with a tmpfs mounted over `/tmp/.X11-unix`; namespace teardown must leave the shared directory's mode and contents unchanged. Xvfb listens only on local Unix sockets (`-nolisten tcp`) and uses `-ac` only inside that private server.

Run setup before formal execution. If setup fails, preserve it as setup/STOP evidence; do not execute the candidate. If the candidate starts, this allocation is consumed even if it fails. Never rerun candidate or mutate raw output.
