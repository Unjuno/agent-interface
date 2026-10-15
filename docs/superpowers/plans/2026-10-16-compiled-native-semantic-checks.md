# Native semantic dependency checks

**Goal:** Close the False/unknown pre-input counterexamples retained in
`research/integration/compiled_semantic_press_boundary_20261016/README.md`.

**Architecture:** Extend the existing input_guard's frozen binding with explicit
interaction (default keyboard, preserving existing users). Compiled execution
registers this guard for every valid authorization. Its trusted perception
callback checks the action symbol's identity/dependencies on fresh native RGB;
the bridge retains association, freshness and original-deadline fences. Releases
never invoke the callback. Post-action effects and entry branch conditions are
not held invariant during task input.

**Constraints:** Local/Fake X only. No live GUI/provider/WSL/allocation. No general
real-time or independent semantic oracle claim. Missing guard capability must
fail before input; callbacks receive copies and are trusted read-only code.

- [x] Reproduce False/unknown before Submit, including click/move/keyboard,
  as failing tests against the actual bridge/store/session. Include stable
  controls, loss of identity, exception, and dependency loss while a key is held.
- [x] Extend input_guard without changing default keyboard compatibility.
  Freeze interaction/offset/tail and refuse mismatches. Connect compiled
  symbol dependencies with retained fresh evidence; preserve release and expiry.
- [x] Run affected normal/-O suites and original-source controls, audit saved
  evidence, retain first failures, and review the immutable publication.
- [ ] Integrate under actual branch protection and exact-main checks, update
  shared entry points and clean only this task's integrated refs.
