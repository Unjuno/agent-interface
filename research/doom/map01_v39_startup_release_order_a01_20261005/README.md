# V39 opt-in startup closure release-order construction A01

This construction tests the exact V39 opt-in selector source together with V15's actual telemetry backend and its owner-v4/runtime owner-v12 release path. It resolves whether A02's two between-up keymap queries are present in that closure.

The successful corrected candidate used frozen main `b347d6f1ede81f6980932f2d7cba6d4758bf49c9`. It emitted two input admissions followed by SPACE-up and F8-up receipts. Each release carried one verified owner-thread `KeyRelease`/`XSync` receipt, both were in one V4 release batch, and the post-batch owner state was empty. The operation trace contained one `sync` and zero `query_keymap` operations between the two key-up injections. The independent audit passed with no errors.

A02's two keymap queries came from the nested V12 transition adapter in its own V4 fixture. The current V39 opt-in closure uses `research/live_control/input_owner_v12.py`, which records owner-thread release receipts and does not sample per-key keymap occupancy. Thus the exact closure does not reproduce A02's query interval. It also does not provide per-key physical actuation IDs or occupancy evidence in this result.

Two failed attempts that supplied the different nested A02 owner module are retained as `results/STOP.json`; they are harness-source mismatches, not production failures. The corrected one-shot output is `results/a03/RAW.json`. The raw trace and result were independently checked by `audit.py` against `FREEZE.json` and current source hashes.

Re-run the read-only audit with:

```powershell
python research/doom/map01_v39_startup_release_order_a01_20261005/audit.py
```

The audit prints its current reconstruction to stdout and never replaces the retained `results/AUDIT.json`. `build_freeze.py` prints a proposed freeze to stdout and never replaces `FREEZE.json`; review and save any new freeze as a separate run artifact. `test_readonly_tools.py` checks both preservation guarantees.

The corrected candidate has already run once and is retained; do not invoke it again as an experimental retry. The `candidate.py` source is included so the seam and call path remain reviewable.

Scope: deterministic fake X display and one two-key sequence. The V39 selector is checked from its exact source; V15 backend, typed-release-v2, release-batch backend, owner-v4 and runtime owner-v12 sources execute. The typed command interpreter/capture superclass is a deterministic seam. There was no full V39 process launch, live X11 or OS input, DoomGame, model call, application effect, latency bound, recovery, threat-response, or MAP01 result. The fake-display sample is construction evidence only.
