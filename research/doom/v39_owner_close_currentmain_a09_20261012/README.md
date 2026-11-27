# Current-main V39 owner-close check (A09)

This additive result checks the V39 input-owner close path after current-main V12/V3 changes. It uses one isolated Xvfb client and the exact current-main V12/V4→V3 composition.

The frozen test admits `a` once, observes its X11 KeyPress, closes the wrapper, then requires the matching KeyRelease, observer keymap-up state, one verified empty close receipt with a matching per-key release attempt and intent token, a stopped owner thread, and Xvfb exit 0. The candidate is one-shot; see `PREREGISTRATION.md` and `FREEZE.json`.

The WSLc image is built from the locally cached digest-pinned Python base. Dependencies are installed during image construction; candidate execution uses `--pull never`, `--network none`, one requested CPU, a read-only package mount, and a separate writable output mount. The host warns that swap-limit support is unavailable, so the configured memory is not a measured hard cap.

This synthetic X-server result cannot establish physical keyboard release, real desktop/game event consumption, task feedback, bounded recovery or Issue #59 completion.
