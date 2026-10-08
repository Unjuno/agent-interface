# Issue #6301 T0 freeze — effect versus task-terminal feedback

**Allocation:** `EFFECT-TERMINAL-FEEDBACK-6301-T0-20261002-01`  
**Issue:** https://github.com/Unjuno/agent-interface/issues/6301  
**Main source snapshot:** `eba652642a7a741d57bbdfe0c1a9929d3b15bd7f` (last-minute refresh from `485985a2819634ee50b0172ca45c9a650ec49206`; main advanced with the #59 repeated-key occupancy record, which does not alter this independent fixture; no formal command had run)  
**Runtime:** Arch Linux WSL2 home filesystem (`/home/unjuno`), WSL Containers 3.0.1 on WSL 3.0.1.0; pinned `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (linux/amd64). Formal candidate and audit run inside disposable WSLc containers from read-only Linux-native source mounts.

## H / T / D / C / U

- **H:** A truthful, typed effect cue can report a verified effect while preserving unresolved terminal obligations; it must not turn that observation into task completion. A generic early “success” display is ambiguous, and late-only feedback withholds an already verified effect. This method test makes no claim about any model's interpretation or proposal behavior.
- **T0:** Deterministically enumerate nine synthetic traces across A (early generic display), B (typed effect plus pending obligations), and C (terminal-only display). Traces cover effect-before-release, release-before-effect, accepted-but-ambiguous save, failed verification, unresolved collateral effect, cancelled input awaiting release, fully terminal success, a truly independent next task, and a stale-generation effect receipt. Each trace carries task/source/generation and obligation IDs. A separately written auditor reconstructs current-generation effect truth, terminal status, and cue fields from the frozen fixture.
- **D:** `PASS_METHOD_SCOPED` only if all 27 trace×display rows match the independent oracle; unresolved obligations and task/source/generation bindings remain identical across displays; effect observation never discharges an obligation or implies task-terminal success; no accepted input/operation is promoted to effect; stale-generation effects remain UNKNOWN; the independent task's obligations do not inherit another task's state; and all four frozen mutations are rejected.
- **C:** Existing #5817 obligation presentation may already be sufficiently typed; generic checklists may perform as well; this finite truth table cannot predict model response. WSLc memory limit was accepted but swap/cgroup memory isolation is unavailable on this kernel; no peak-memory guarantee is needed or claimed for this small CPU run.
- **U:** Entirely synthetic and deterministic. No human cognitive mechanism is transferred to LLMs; no model, GUI, provider, user data, actual task, action, or safety performance is tested. The generic display is a counterfactual stimulus label only and is not emitted to a model or runtime.

## Frozen truth rules

1. An effect is current only if its receipt generation equals the task's current source generation; accepted input is not an effect.
2. `task_terminal=SUCCEEDED` requires a current verified target effect, independent verification PASS, release VERIFIED, collateral CLEAR, and zero open required obligations.
3. Any missing/UNKNOWN/PENDING required obligation keeps task-terminal status PENDING. Feedback text never changes the truth table.
4. Every display row carries the exact same evidence envelope for a given task: task ID, source ID, generation, effective effect status, and complete obligation IDs/statuses.
5. Independent tasks are scored independently; their obligations are neither merged nor discharged by the other task.

## Frozen traces

`fixture.json` has nine traces: `effect_before_release`, `release_before_effect`, `ambiguous_save`, `failed_verification`, `collateral_effect`, `cancelled_input`, `no_pending_obligations`, `independent_next_task`, and `stale_effect_generation`. Displays A/B/C and all expected status semantics are frozen before candidate execution. Four mutations: drop a pending obligation, forge task-terminal success, accept a stale-generation effect, and equate accepted input with effect.

## Frozen execution

Run `wslc_smoke.sh` from the Arch WSL home to check a Linux-native read-only bind and cleanup. Run construction-only syntax/fixture tests once before formal. Then run candidate exactly once and, only after candidate exit 0, the independent auditor exactly once. Use WSLc `--pull never --network none --cpus 1 --memory 512M`, a read-only Linux-native source bind, stdout-only outputs captured in the WSL home, and `--rm`. Do not use Docker, GUI, GPU, models, network during formal runs, retries, or threshold tuning. Preserve all output and exit statuses as-is.

