# Formal allocation 03 — STOP

This is the immutable result of the single authorized invocation for allocation `issue5236-formal04-20260930-01`. Do not rerun, replace, or continue this output.

- Frozen source commit: `822a48af18c349ea2b2053f7cccfe92f7f8c3a67`.
- Wrapper exit: 2; timeout: false; host WSLg socket metadata unchanged.
- The child successfully created a private mount namespace and tmpfs at `/tmp/.X11-unix`; source manifest checks passed.
- Exactly the first `control_us` row began. Xvfb `:0` was started, US layout setup/readback passed, and Xvfb exited naturally with status 0 during cleanup.
- Fixture exited 1 before any program dispatch or remap actor launch. Its preserved stderr reports `ImportError: libtk8.6.so: cannot open shared object file` while importing `tkinter`.
- No subsequent row ran. There is no saved application effect or actor receipt. No Xvfb/fixture/actor process remains.
- `raw.json` and `wrapper.json` retain the row, exact stderr, command, hashes, namespace/mount, socket metadata and independent Xvfb exit status.

Classification: `STOP_PROVENANCE_OR_RUNNER` (formal target environment lacks Tk runtime library). This allocation is immutable. A corrected environment and any later invocation require a new additive successor allocation, fresh output path, and a new Issue freeze.
