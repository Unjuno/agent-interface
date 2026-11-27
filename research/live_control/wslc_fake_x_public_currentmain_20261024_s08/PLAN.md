# S08 — Fake X WSLc runner diagnostics

S06 is immutable and remains HOLD: the dedicated WSLc session, pinned image and container started, but the process exited 1 without observable stdout. S06 subscribed only to `OutputReceived`; it did not retain the distinct `ErrorReceived` stream. S08 changes the harness to retain stdout and stderr separately, with each event also emitted to the host receipt. It does not reinterpret S06 or retry its session.

**H/T/D/C/U:** H: using the SDK's separate Event-mode error callback will identify whether S06 exited before Python runner startup; if startup proceeds, current-main Fake X cases may complete. T: build to a new short native-DLL path, check immutable source/dependency freezes and exact empty output/new storage, then run exactly one newly named session, one digest-pinned image pull and one no-network container. D: scoped PASS requires both normal and optimized 26-check/4-mutation saved audits, reconciled outputs, and confirmed exact cleanup; otherwise HOLD/UNKNOWN with no retry. C: API may still fail before stderr capture; event timing or mount/startup problems may remain unclear. U: memory-only Fake X; no real X, physical input, GUI, app, cancellation, release bound, recovery, task effect, MAP01 or efficiency claim.


S07 diagnosed the missing /deps insertion on the current runner interpreter path. S08 adds /deps to sys.path before importing Xlib; no other probe behavior is changed.

