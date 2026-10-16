# Executor Child SIGKILL with Persistent InputOwner Xvfb A04

## Scope and pre-registration

A04 corrects A03's independent event watcher to subscribe with X KeyPress/KeyRelease **mask** bits, while retaining A03's corrected direct reference to the underlying V12 owner. A02 and A03 remain STOP and are not rerun.

- **H:** A resident InputOwner V4/V12 in the supervisor process can observe RPC EOF from a SIGKILLed Executor child and release its tracked Xvfb key.
- **T:** A focused Xvfb window, actual current-main Executor V3 in a child process, and current-main InputOwner V4/V12 resident in the supervisor. Confirm keydown; SIGKILL only Executor; verify IPC EOF; close the owner; record owner release receipt, independent KeyRelease, keymap-up, and owner thread shutdown. One invocation.
- **D:** PASS_METHOD_SCOPED requires every frozen gate in `FREEZE.json`, including frozen hashes, active down before kill, SIGKILL, EOF before owner close, verified empty owner-release record, independently observed KeyRelease, keymap-up, stopped owner thread, and clean Xvfb exit.
- **C/U:** The Xvfb/local socketpair supervisor pattern is a prototype, not current production session topology. No live application, game, model, physical input, or live allocation. WSL2; no hard CPU/memory cap or network namespace.

## Result

**PASS_METHOD_SCOPED.** The candidate ran once, exited cleanly, and the independent raw-only auditor passed all 11 checks. X KeyPress was observed at 215,234,345,889 ns; the worker SIGKILL request followed 295,817 ns later. The supervisor observed RPC EOF 281,000 ns after kill. Owner close began 1,158,293 ns after kill; its XTest KeyRelease/XSync attempt began at 215,235,960,332 ns. A separate X connection observed KeyRelease at 215,236,195,879 ns; the owner keymap sample verified up at 215,236,283,477 ns. The owner release record was verified with empty key/button state, and the owner thread stopped.

Together with hard-kill A01, this shows a concrete recovery boundary in the fixture: killing the process that owns both Executor and InputOwner leaves the Xvfb key down; killing only an Executor child while a separate supervisor retains InputOwner lets the supervisor detect EOF and release the tracked key. This supports an independently resident input owner/supervisor as a recovery direction.

It does not prove production integration, supervisor crash recovery, multi-window/process arbitration, scheduling reliability, semantic perception, or task success. The current production session topology still needs a source-level integration design and end-to-end test. See `AUDITOR/audit.json`, `results/A01/RAW.json`, and `FREEZE.json`.
