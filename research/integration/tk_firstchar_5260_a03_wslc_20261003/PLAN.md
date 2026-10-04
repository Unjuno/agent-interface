# #5260 A03 readiness epoch successor — construction plan

Purpose: correct and verify the readiness callback reentrancy discovered
in consumed A02, before any new first-character allocation. Old A02
sources/results and its stronger STOP remain immutable.

This is an additive private draft, not the A02 PR or a formal allocation.
The same human autonomous-container direction applies; no other owner's
branch/runtime or old consumed row is reused.

1. TDD a small readiness state machine that claims before the callback
   capable of reentry, schedules one finalizer, and fails closed after errors.
2. Integrate it into a derived app in a new A03 path/branch after A02
   evidence delivery. No default wait or automatic key replay.
3. Perform a separately labelled no-input private-Xvfb construction,
   retaining legacy/fixed callback counts and immutable ready-file identity.
4. Only after source/receipt/image/epoch checks and independent controls,
   freeze a NEW input allocation; do not rerun A02.

H: claiming readiness before update_idletasks prevents duplicate finalizer
and decoy focus scheduling caused by reentrant Map/Configure callbacks.
T: callback unit adversaries, then fresh Tk apps without XTest input.
D: one finalizer/unchanged first ready epoch for corrected app; first outcome
retained if failing. Construction does not qualify first-character delivery.
C: same pinned WSLc image, private display, no user desktop/network/GPU.
U: disposable Tk, not the real public client or useful-feedback qualification.
