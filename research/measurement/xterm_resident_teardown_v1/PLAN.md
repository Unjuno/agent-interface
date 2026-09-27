# #4448 — resident XTerm teardown experiment

## H — hypothesis

Keeping one XTerm and one fixture child alive for four Return actions removes native XTerm exit from each action's critical path. With the same private display, XTEST input and independent effect/keymap observer, it should preserve exact effect bytes and neutral key state while reducing effect-observed→next-action-ready latency. The single final resident teardown remains separately measured and included in the resident arm's session duration.

## T — treatment and protocol

- One private Xvfb/Openbox pair per matched pair; one XTerm/child at a time.
- `EPHEMERAL_XTERM`: four actions, each in a fresh XTerm and fresh child. The child exits after its one exact effect record; next-ready is recorded only after native XTerm exit.
- `RESIDENT_XTERM`: one XTerm and one looping child for four actions. Readiness after each action requires the append-only effect receipt and an all-zero independent XQueryKeymap snapshot. XTerm/child exit after action four is separately timed.
- Both arms send the same XTEST `r` press/release followed by Return press/release. Each effect line is byte-identical `{"value":"r"}\n`; only the child loop limit differs. The observer polls retained effect bytes and samples XQueryKeymap.
- Twelve matched pairs × four actions/arm = 96 formal actions. Arm order alternates exactly as frozen in `SCHEDULE.json`. Each arm/action has isolated effect evidence. Parent `perf_counter_ns` timestamps are authoritative.
- Retain exact effect bytes/prefixes and hashes, ready/done child receipts, XTerm/child/Xvfb/Openbox PIDs and exits, input/keymap receipts, timestamps, stderr and cleanup.

## D — decision

The exact machine-readable gates are in `GATES.json`. PASS requires 48/48 exact effects and neutral keymaps in each arm, reconciled exits/cleanup, one resident XTerm and child throughout actions 1–4, resident p95 <30 ms, ephemeral p50 >100 ms, paired median latency ratio ≤0.35, resident session duration lower in at least 10/12 pairs including final teardown, independent audit errors empty and at least 10 effective copied-evidence corruptions rejected.

Correctness or release mismatch is FAIL. Valid evidence with timing gates not met is HOLD. Missing process/raw/audit evidence is HOLD/STOP. No threshold, endpoint or inclusion rule is changed after formal execution. Construction data is excluded.

## C — caveats

This changes lifecycle: ephemeral readiness waits for native XTerm exit; resident readiness does not. It is an interface-factor comparison, not equal-terminal-endpoint microbenchmark. The fixture has only the child-local loop counter; hidden application state remains possible. Parent polling may perturb scheduling. XQueryKeymap reports X-server logical state, not physical HID telemetry. Inference is limited to the exact locally cached Docker image and this Xvfb/Openbox/XTerm fixture.

## U — out of scope

No claim about model/task usefulness, arbitrary applications, public CLI integration, crash/restart, memory leaks, long-session stability, token/human-tempo benefit, or production authorization. A PASS informs later benchmark endpoint accounting; it does not itself authorize/promote a resident runtime implementation.

## Execution and integration

All experiments and audits run on the local Docker Engine with the pinned cached image, `--pull=never --network none --read-only`, and ephemeral tmpfs for `/tmp` and `/dev/shm`; no GitHub Actions/workflow is scientific evidence. Freeze code, exact schedule/gates and environment on the owned branch and read them back from GitHub before exactly one formal Docker invocation. Run the independent raw-only audit and copied-evidence corruption controls in Docker. Publish the exact raw artifacts and report in this additive path, open a PR, inspect exact-head review/status, and merge only verified evidence.
