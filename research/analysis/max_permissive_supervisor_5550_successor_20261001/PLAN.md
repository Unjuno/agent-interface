# Issue #5550 successor allocation 03 — execution-gated finite supervisor replay

**State: preparation only; no allocation or formal execution yet.** This is a new reproducibility allocation after `STOP_ALLOCATION_WINDOW_EXPIRED` in the predecessor record. It will not overwrite or relabel the predecessor raw/audit. No container may launch until #5085 records an explicit owner, exact non-overlapping window, image digest/platform, and coordinator assignment.

## H / T / D / C / U

- **H:** Replaying the same finite, fully observed DFA with a valid serialized CPU-only container slot will reproduce the predecessor's exploratory policy counts: fixed-point synthesis is safe/nonblocking and admits more bounded successful traces than fail-closed, while greedy allow-list exposes stale-commit and duplicate-effect transitions.
- **T:** Freeze current main and exact candidate/auditor source blobs. Run seven local launch-guard tests. At the exact granted slot, require guard PASS (assigned lease, current-main match, approved image/platform, empty active-container inventory, current UTC inside the half-open interval). Only then run one network-disabled candidate container and, if exit 0, one separate raw-only auditor container. Write only to this successor directory.
- **D:** `PASS_T0_SYNTHETIC_SCOPE` only if the launch guard passes inside the assigned window, raw-only replay is complete/error-free, synthesis has zero unsafe transitions and more safe completions than fail-closed, and greedy rows include stale-commit and duplicate-effect counterexamples. Any failed launch guard is a pre-invocation STOP; any formal container failure consumes the successor allocation and is not retried.
- **C:** Any apparent recovery advantage may be entirely due to the hand-authored REACQUIRE transitions; real partial observation can require fail-closed behavior.
- **U:** Same finite, fully observed synthetic plant only. No real GUI, event classification, timing, task effect, production supervisor, utility, latency, or transfer claim. Repetition is for a valid, serialized execution record, not an increase in scientific generality.

## Protocol repair

The previous allocation's frozen interval expired before its runner/auditor began, and active other-task containers were observed afterward. The new package will include an executable `launch_guard.py` that checks exact coordinator-assignment fields, current main, image digest/platform, empty container inventory, and a half-open UTC window before any Docker command is invoked. Guard failure writes no formal candidate/audit output and authorizes no retry.

## Pending before freeze

1. Coordinator assigns a fresh non-overlapping window and cached image/platform in #5085.
2. Refresh current `main`, issue/PR/branch collisions, and confirm the new successor path is unused.
3. Freeze the predecessor candidate/auditor source blob + SHA-256 dependencies and the guard/test sources.
4. Freeze exact commands, lease comment ID, and output paths; commit the preregistration before the slot.
5. At slot start, recheck time, main, image/platform, and Docker inventory; run the guard, then at most one candidate and one conditional raw-only audit.

No completion, pass, or retry is claimed by this preparation plan.
