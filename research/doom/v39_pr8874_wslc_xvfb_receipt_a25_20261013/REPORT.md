# Current workspace V39 backend receipt and terminal-clear A25

`PASS_METHOD_SCOPED`. Using the exact edited workspace backend source, the WSLc/Xvfb run observed the `w` KeyPress/KeyRelease pair, server keymap down/up, a verified V4/V12 batch release, and one analyzer-accepted hold. It then invoked the backend's terminal `release_all()` path, observed verified terminal release, and confirmed the admission cache contained zero entries afterward. Owner stopped, Xvfb exited 0 and the disposable container was removed.

A24 had already passed the receipt-link composition; A25 specifically uses the current workspace implementation including terminal cache cleanup. The game-specific parent was stubbed with `release_all()` delegated to the real owner, so this remains a backend/owner/analyzer integration experiment rather than full Doom/MAP01 execution. No physical input, task effect, threat, recovery-efficacy, or live allocation claim.

Preregistration and hashes are in `PREREGISTRATION.md` and `SOURCE_MANIFEST.json`; raw SHA-256 `ba4f38e2d76bde7f6b6e905ab0afee914018002b25e5b18a4ff8e513d91a92fc`, independent checks `results/a25-01/audit.json`.
