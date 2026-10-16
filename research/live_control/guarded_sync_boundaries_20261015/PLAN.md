# Remaining synchronous guarded-input boundaries (Fake X only)

Base: main `6ca6adc51618d02765afd2de97b25a96dadffe95` (#8939).
Question: does opt-in target-query separation also keep cleanup responsive when
an additional visual input guard captures, persists or calls trusted code while
CTRL is held? Hypothesis: those synchronous boundaries still prevent cleanup.
This is a finite construction characterization, not a live allocation or fix.

Use actual NativeHandleBridge construction, observe/mint, input_guard,
cancellation_scope, keyboard, public dispatch/session/backend and release ledger.
Reuse the existing FakeX transport fixture; setup/preflight/backend focus are
fake. The named focus/process reader returns immediate fake evidence. No real
display, input, WSL/container, model or application. A forged fixture identity
does not qualify local-server/PID-namespace correspondence or a task effect.

Frozen matrix (once per normal/optimized Python): healthy, then capture,
observation persistence and trusted callback, each with cancellation or original
deadline expiry. The guard checks the same CTRL+a program. Gate only when the
fake CTRL prefix is already held; no other task key is down. After gate entry,
request actual cancellation or advance the fake monotonic clock to the original
deadline, snapshot before releasing the gate, then let the caller finish.
All waits have a five-second harness cap and unconditional finally unblocking;
the cap is not a measured release bound. Preserve first outputs, refusing overwrite.

Decision fixed before execution: healthy must complete CTRL+a and verified fake
cleanup. Every blocked case must show CTRL held, no returned result/cleanup and
no following a press while the gate is closed. Cancellation must acknowledge a
request without claiming release; expiry must reach the original deadline.
After gate resumption, all blocked cases must fail and release CTRL with verified
fake-neutral state, without a press of a. Otherwise retain the disagreement and
do not call the characterization successful. A PASS supports a counterexample
to full observation/control-plane isolation, not a physical-release guarantee.

Keep each actual bridge directory, raw summary, source hashes and raw-only audit.
Auditor mutation controls must reject missing held state, claimed early return,
post-cancel task press and unverified final release. Next decision: identify a
complete immutable capture/reply association seam and separate side effects;
moving a shared input connection onto another thread is not an acceptable fix.
