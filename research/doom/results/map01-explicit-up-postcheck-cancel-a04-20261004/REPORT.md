# A04 first outcome

Classification: `REPRODUCED` for the frozen software boundary hypothesis.

The forced queue schedule yielded an owner false cancel sample at `100986741656000 ns`, queued `up` dequeue at `100986741690500 ns`, and cancellation set at `100986741691041 ns`. The owner-thread `KeyRelease` began at `100986741694958 ns`; fake XTest observed the cancellation event already set at the side effect (`100986741696541 ns`). The caller transition still reported `cancel_requested_at_request=false` and `ordinary_release_candidate=true`, and v4 joined one identity-bound owner key-up receipt (`owner_thread_keyup_verified=true`).

The candidate exited 0. Its after-up input-state sample reports no owned keycodes, the fake keymap has keycode 30 up, and the subsequent cancellation cleanup record is verified with an empty keymap. The saved raw-only audit passes with all three negative controls rejected.

This demonstrates that the v4 ordinary-release candidate flag is based on cancellation state at caller request time; it does not classify a cancel that becomes set after the owner's pre-dequeue poll but before the owner-side key-up. The schedule is forced once, so it does not estimate frequency. It is a host Python/fake-Xlib construction against the PR #7441/#7449 source stack, not current-main runtime evidence, real X11, physical input, application consumption, useful task effect, or live recovery. OrbStack's daemon failed before candidate execution, so this does not qualify container portability.

Earlier A01 and A02 are harness STOPs. A03 captured the same ordering but stopped in its fake post-up pointer query; its original audit failure and separate audit-v2 adjudication remain preserved. A04 adds only the missing fake pointer coordinates and supplies the complete construction result.
