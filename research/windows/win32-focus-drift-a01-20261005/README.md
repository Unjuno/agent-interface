# Win32 focus drift fence A01

## H / T / D / C / U

**H.** In the Win32 backend, `focus()` verifies a target HWND once. If the
foreground changes before a later keyboard action, the backend can still send
global `SendInput` events to the newly foreground window. Rechecking the
registered HWND immediately before each normal input insertion should stop
that stale-target path while preserving unconditional release cleanup.

**T.** Run two deterministic tests through `Win32RuntimeSession.dispatch()`
with an inert `SendInput` fake. First, switch the foreground to another fake
HWND immediately after `focus()` reports success and verify that no DOWN is
sent. Second, switch foreground after a DOWN and verify that the subsequent
normal UP is refused, cleanup UP is still sent, and the session reports both
the execution failure and verified empty release. No OS input or app is used.

**D.** The parent must fail both regression cases; the candidate must pass both
and the focused Win32 cleanup, transition, GDI helper, and core-contract suite.

**C.** The existing one-shot Win32 host smoke and fixture-app integration do
not inject focus loss between focus verification and later input. `SendInput`
is global, so an asynchronous foreground transition is a relevant integration
boundary even when a target HWND was initially verified.

**U.** This is a deterministic software composition test. A foreground sample
cannot eliminate the residual check-to-`SendInput` race. It does not prove
physical keyboard state, delivery to the intended application, task effect,
reliability under real focus churn, or broad desktop control.

## Result

Against parent head `ef190e1037ff2f9df0cb2e941578a79a9fe0019b`, both tests
fail: the session reports `completed` and includes a normal action after focus
drift. On the candidate, both tests pass. The combined focused suite passes
56/56; exact command output, exit status, and source identities are retained in
the adjacent result package. No live application input was sent in this study.

The candidate checks foreground identity before each normal `SendInput` and
before pointer movement. A focus mismatch fails the action and lets the
existing terminal cleanup release held inputs even after foreground changes.
The check narrows the race window; it cannot make the OS focus check and global
input insertion atomic.
