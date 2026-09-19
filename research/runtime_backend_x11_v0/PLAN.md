# X11 backend conformance v0 — finite plan

BASE/stack dependency: portable contract PR #97 retained head `0f2bda3c7d9eb863714795789dcfa2ea9fe86bd5`.

One private Xvfb server, one Xlib event fixture, one X11/XTEST backend instance.

Frozen cases after construction calibration:
1. valid focus/pointer/text/chord/scroll/observe/release program;
2. stale observation: zero XTEST emission;
3. stale binding: zero XTEST emission;
4. expired lease: zero XTEST emission;
5. held key+button then terminal release with physical empty verification;
6. 64 seeded valid focus/move/key/release programs.

Hard PASS: expected admission; three invalid cases emit zero backend input; all accepted programs finish with verified empty tracked physical input; independent fixture observes delivered press effects; captured pixels change after delivered effects; no source mutation after freeze.

No provider/model/network, shared display, formal MAP01 allocation, Windows/macOS/Wayland claim, or production runtime promotion.
