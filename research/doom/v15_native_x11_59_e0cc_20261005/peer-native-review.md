# Independent native-X11 evidence review

This is a read-only coauthor technical review, not a nonauthor quorum vote. I inspected the frozen `run-01/raw.json`, `run-01/audit.json`, `audit_native.py`, `freeze.json`, `vm-freeze-verification.json`, `source-lock.json`, and `PROTOCOL.md`. I did not execute the probe or auditor and did not alter frozen run files.

## Identity and custody

- Frozen source head: `2b0cb591c3ebcb84d1db983612613850c08fffea`.
- Raw SHA256: `923d7ce368cafe7a05b0799d7dbcac5eb39462628099d571c9d2cc4d8d8e3aa6`.
- Source-lock SHA256: `c142db9f35d3420acfb4277efcc44e8fa84a984de334309c9b15af2ef75e9914`.
- Frozen auditor SHA256: `2b396fd8689218eae847cacc5083a9916701291b9501f1ff15b40754d0d4f68b`.
- The retained raw audit reports **658/658 checks passing** and binds the loaded module hashes to the frozen inventory. The VM freeze verifier reports exit 0 with all listed source/package hashes matching.

## Reconstructed behavior

In `ordered_batch`, the X server began neutral, admitted `a`, `s`, `w` in that order, and reported all three down. The focused window received native XTEST KeyPress events for those three keycodes, followed by KeyRelease events in `w`, `s`, `a` order. The owner emitted three complete release rows in the same reverse order, each with a distinct actuation ID matching its DOWN admission. Their measurements use the shared batch snapshot basis; the retained samples and intervals are ordered, and the server keymap was neutral after the batch and after owner close.

In `cancel_cleanup_then_late_up`, the owner admitted `a` and `s`; the test then set the lease's cancellation event. The owner recorded verified `cancelled` cleanup with an empty key set. Each cleanup receipt contains a confirmed UP bracket with `per_key_cleanup_snapshot`, and its owner, token, key, and actuation ID match the original DOWN admission. The window event stream records cleanup KeyRelease events for `a`, `s`. The deferred same-lease batch then raises `Cancelled`; it creates two incomplete `step_exception` rows, with no explicit UP receipt, ordinary-release candidate, or authority. Owner records and test-window input events do not grow after that late call. Keymaps are neutral before the late call, after it, and after close.

Both owner threads stopped, each retained a verified owner-release record with reason `close`, and the observer and Xvfb shut down. The run records Python 3.11.2, X.Org/Xvfb, a private X window/focus, a private network namespace identifier, the process cgroup path and its 1-CPU, 1-GiB memory, zero-swap, 64-task limits. The test was run as UID 501. The namespace reports loopback and tunnel interface names; this evidence does not itself test network egress.

## Scope and limits

The source and raw evidence support a native **virtual-X11 measured-backend component check**: the actual measured V15 backend constructor and current owner chain were used with real Python-Xlib/XTEST operations and X-server keymap queries. The driver directly exercised backend raw/release-batch calls with a program/step context; it did not run the backend's normal `execute` program path. It did not run the V39 controller loop, Session orchestration, game, HUD/image capture, planner/model, or physical display/keyboard. The observed X events and keymap brackets are evidence about this Xvfb server, not hardware state, application consumption, useful game feedback, or gameplay effect. I found no material inconsistency between the raw traces, frozen protocol, and the stated component-only scope.
