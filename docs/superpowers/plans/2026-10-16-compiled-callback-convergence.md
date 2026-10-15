# Converge callback receipt repair #7954

**Goal:** Preserve known completed input/release and both failure causes when
ordinary verifier or post-dispatch journal callbacks fail.

**Sources:** PR #7954 head `f18c378f1eef3f48ea10207e17eb7f184bb5d8a5`
and its terminal-journal self-check comment 6034510392; current main
`b0ffed8920706265adc0d44987556aaf41c78ee2`.

**Architecture:** Adopt the original verifier-exception and journal-prefix tests
with package imports. Adapt the behavioral patch to current core rather than
replace its newer unresolved-execution/association/callback-copy safeguards.
Ordinary post-dispatch journal failure is sticky, never retried, returns typed
failure with prefix; pre-dispatch journal exceptions retain their existing
propagation contract. Preserve private event copies. Record terminal sink
failure even when already failing for another cause. The guarded adapter retains
its original verifier exception witness before core consumes that exception.

**Constraints:** Local/Fake X/inert only; no native/provider/allocation. No durable
publication or recovery guarantee. Fatal BaseException and malformed adapter
returns retain their existing contracts.

- [ ] Adopt original test ideas and add compound terminal failure, mutation,
  no retry, prefix/release and caller-composition regressions; retain RED.
- [ ] Apply the focused current-source repair, preserving pre-input/fatal and
  malformed-return behavior. Run selected normal/-O checks and exact old-source
  controls, retain source/conditions/raw and readback evidence.
- [ ] Review/integrate, preserve the old PR's original bytes and unresolved
  scope, then close only that now-converged PR with a concrete continuation.
