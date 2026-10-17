# First native construction: application-effect gate failed

**FAIL_OR_HOLD — no native application-prefix confirmation.** Frozen source commit `2081bb759203da1f8c5cb9e96c49c79972344e80`, prospective #57 comment6040850590, exact #8308 backend/core/sequence `dae92e12097907e860f68d6ee22a10cb23ace442`. All six first cells ran once, driver/service exits 0; no replacement input or post-result actor changes. The frozen auditor executed 99 checks and recorded 12 failures, all application text/event checks. Its failure is retained unchanged.

| Condition | Gap (ms) | Receipt | Expected Tk text | Actual Tk text | Text XTEST requests |
|---|---:|---|---|---|---:|
| held a | 0 | execution_failed, op 2 | a | empty | 0 |
| held a | 20 | execution_failed, op 4 | ab | empty | 2 |
| no held key | 0 | completed | ba | empty | 4 |
| no held key | 20 | completed | ba | empty | 4 |
| held SHIFT | 0 | completed | AB | empty | 4 |
| held SHIFT | 20 | completed | AB | empty | 4 |

The native request/receipt distinction reproduces: unpaced held-a refuses its text before any text request; paced lowering sends the b press/release before refusing a. The independent observer sees the intended held keycodes, and final/post-settle keymaps are neutral. This remains request-boundary evidence: it does not establish that b entered the application.

All six independent Tk records have `focused="None"`, `events=[]` and an empty Entry, including the no-held positive controls. The fixture called `focus_set()` and the backend verified X focus on the Entry window, but no Tk focus/readiness acknowledgment was required before input. **Inference:** a recipient/focus readiness defect is a leading explanation. Exact causal mechanism is unproven; neither increasing waits nor replaying cells was used to turn this result into support. Backend focus success and clean completion are insufficient application-effect evidence here. The original #8308 paced refusal review remains based on its independent inert probe and this native request journal, not successful Tk delivery.

Effective run gates: CPU quota 1, 512 MiB RAM, no swap, 128 tasks, UID 501, source unwritable, only loopback active/no IPv4 route. Six application and six Xvfb processes exited 0 without forced kill; display sockets/locks removed, input readback neutral, no experiment processes left, transient unit inactive/dead. Owned VM `01M4BD6K3B8BGXMVYA7RMM128R` was stopped after evidence export; disk retained. No foreign VM, shared daemon or real desktop was operated.

Preparation record: private Docker build failed at nested cgroup BPF permission; source import closure, observed UID, and ineffective ProtectSystem were repaired before freeze without input. Root-owned read-only source permissions passed preflight05. No Docker success or effective ProtectSystem/PrivateTmp mount protection is claimed. Exact dependencies and source bytes are retained. There is no full CLI/session/model/physical-keyboard/game/task-success or reliability/latency claim.

Six saved-data mutation controls each introduced and detected a specific additional failure (missing invocation, nonzero driver exit, nonneutral keymap, absent prefix requests, nonzero app exit, modified source). Because the real baseline already fails, these establish sensitivity of those checks, not a successful end-to-end positive fixture.

## Read-only verification

Run `python3 verify_saved.py` from any directory. It verifies archive/member identities, unpacks only temporary copies, imports only the saved-data auditor, and confirms the original 99-check/12-failure report. It never launches run.py, Xvfb, Tk or native input. A successful preservation verification is not scientific PASS.

Next useful work is a separate bounded fixture-readiness diagnosis that distinguishes X focus, Tk focus and actual delivery before any new hypothesis experiment. The consumed six cells remain final. This additive preservation proposal needs fixed genuine nonauthor review and current-main combined-tree/gate checks before main; root is its author and has no self-approval vote.
