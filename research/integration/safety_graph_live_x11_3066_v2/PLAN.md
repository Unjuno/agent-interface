# #3066 live X11 runtime dependency/fault allocation v2

Allocation: `safety-graph-live-x11-3066-20260923-01`. Base main: `030b9f9c7c753674c4f25835f29a6803386e9e15`.

## H
A current-main-derived X11/XTEST runtime slice either reconciles with the declared safety graph and preserves timely independently observed release under the frozen faults, or live traces expose a hidden dependency, late/unverified release, or evidence gap.

## T
Two private display configurations: bare Xvfb and Xvfb+Openbox. Seven schedules each, exactly once: normal, ipc_delay, display_stall, owner_death, target_replacement, cleanup_failure, unknown_dependency. Same F8 action; 150 ms authority deadline; normal release after 30 ms. Tk KeyRelease timestamp is the independent timely-release witness; XQueryKeymap is terminal actuator-state evidence. The executed slice copies the current `X11Backend` focus/key/release Xlib/XTEST semantics; complete current-main backend/session/contract Git blob IDs are separately frozen as provenance. No model/provider/network/user desktop.

Declared nodes include caller/runtime/core-admission, Python process/scheduler, backend preflight, X11 connection/server/XTEST, target, release, independent app/keymap observers and cleanup. Owner death adds cleanup supervisor; IPC delay adds result channel. Unknown dependency must type-stop before input.

## D
Use #3066 vocabulary without relaxation. `PASS_SAFETY_GRAPH_RUNTIME_RECONCILIATION_SCOPED` only with 14/14 reconstructible process/timing/effect/cleanup rows, no undeclared dependency, and all bounded faults independently observed released by deadline+50 ms. Hidden dependency => `FAIL_SAFETY_GRAPH_HIDDEN_DEPENDENCY`. Missed/late/duplicate/unverified release => `FAIL_SAFETY_RELEASE_LATE_OR_DUPLICATE`. Missing independent release-time or graph/process evidence => `HOLD_SAFETY_GRAPH_EVIDENCE_INCOMPLETE`. Setup failure before first fault => `STOP_SAFETY_INFRASTRUCTURE`.

## C
SIGSTOP, SIGKILL, target termination and forced release failure are directed faults. Openbox is only a second display configuration. X-server key state is not physical HID. The extracted slice is not execution of every current runtime module; exact source identities are frozen so this limitation remains auditable.

## U
No general GUI safety, physical-device, cross-platform, hard-real-time, model/task, token/latency, or production-readiness claim. A FAIL is retained without retry/tuning.
