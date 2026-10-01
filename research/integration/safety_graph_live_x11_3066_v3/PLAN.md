# Issue #3066 successor allocation v3

## H/T/D/C/U

- **H:** The promoted X11 runtime's process/display dependency graph and terminal physical-input release behavior are not fully demonstrated by the retained #3066 evidence. The previous frozen allocation stopped after 6/14 cases and used a behavioral slice instead of the current runtime facade.
- **T:** Current-main `runtime.cli_v1.api.dispatch` at `da411bf55844fe19d1f0ab95f1ff123af7f98d63` with the real `X11RuntimeSession` and `X11Backend`, against an independently observed X11 application under Xvfb, with bare X and Openbox configurations.
- **D:** 14 unique cells: 2 window-manager configurations × 7 schedules (`normal`, delayed parent pipe read, X server SIGSTOP stall, worker SIGKILL, target-process replacement, injected backend release exception, and unknown dependency).
- **C:** Each cell runs in a fresh X server. Only the `normal` baseline contrasts with perturbation schedules; unknown dependency is a typed no-dispatch stop control. Formal denominator is new and independent of the prior 6/14 allocation. No pooling, replacement, rerun, or tuning after freeze.
- **U:** Raw process snapshots, parent/child PIDs, `/proc` fd links, `/proc/net/unix` socket paths, independent target key events, X server keymap transitions, worker dispatch receipt, authority deadline, cleanup return codes, and container/image/source/gate identities. An independent auditor derives PASS/FAIL/HOLD from raw evidence.

## Acceptance boundary

The scoped pass requires all 14 unique identities, exact current runtime class/facade evidence, unknown dependency stopping before a worker exists and with no input down, all worker and external-supervisor recovery paths returning F8 up no later than deadline + 50 ms, and no unclassified Unix socket dependency in the observed process graph. Missing/incomplete evidence is HOLD. An observed hidden dependency or late/duplicate release is FAIL. A fail or hold is still a completed research result; it does not close Issue #3066.

The fixed matrix checks one synthetic F8 key on Xvfb/Openbox. It does not establish safety for physical desktops, other keys/buttons, GPU/input stacks, or application task outcomes.

## Frozen execution

One formal invocation only, after public freeze and hash readback. No command-line cell selectors exist; the runner must produce the complete 14-cell matrix or preserve a typed STOP record. Container networking is disabled, root filesystem is read-only, source/gate mounts are read-only, and only `/work` is writable. Construction probes are explicitly excluded from formal evidence.
