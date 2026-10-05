# Issue #59 A01: V15 two-key release ordering

## Question and decision

Does the V39 opt-in V15 input/release composition issue both explicit key-up operations before a terminal owner-state sample, or does it query the keymap between keys? What does its sample establish?

Keep V15's back-to-back release ordering and per-key identity-bound XTest/XSync receipts. The post-batch `input_state` sample establishes an owner-reported empty state after both explicit release calls; it does not establish physical state after each edge or target-application use. Do not insert per-edge probes into this path without measuring their effects on release ordering and latency.

## H/T/D/C/U

- **H:** the selected release composition executes two explicit `up` calls in order, each with its own owner-thread XTest `KeyRelease`/`XSync` identity receipt, then one `input_state` call. No `query_keymap` occurs between those explicit releases. Owner cleanup may independently call `query_keymap` after the batch.
- **T:** run the current V15 release-batch backend source together with the actual v4→v3→v12 input-owner adapter stack and actual V12 owner-thread code against a deterministic fake Xlib `Display`. A fake outer executor issues two held keys (`a`, `space`). Capture every event on the same process `perf_counter_ns` clock. Inject an inter-key `input_state` negative control. A second harness run isolates wrapper publication/order with a fake owner.
- **D:** the full adapter-stack baseline passes all assertions. Order is `KeyRelease(38)`, `XSync`, `KeyRelease(65)`, `XSync`, then one `input_state` RPC. No `query_keymap` is observed in the bounded batch interval. One `query_keymap` occurs later in `owner.close()` cleanup. Both emitted rows carry one matching per-key receipt and set `physical_verification_authoritative=false`. The inter-key sample negative control is detected and fails the one-terminal-sample assertion. The independent evidence audit passes.
- **C:** the r136 A02 `query_keymap` observations belong to its diagnostic retained-V4 backend/adapter construction, not this V39/V15 release closure. Preserve the distinction; do not infer startup behavior across compositions.
- **U / limits:** no X server, ViZDoom process, real XTest request, physical keyboard, game effect, or latency claim. The V39 controller selection, session construction and executor loop were not launched: the outer executor/session seam is fake, while the release wrapper, v4/v3 adapters, and V12 owner-thread body are actual pinned source. This resolves source-path ordering only; the physical-latency lane remains unallocated.

## Freeze and reproduction

- Source checkout: `Unjuno/agent-interface` PR head `8a9e76d56be60fdaf96fa87ccbc9c7defd29e20d`; V15 input/release files are SHA-256 pinned in `SOURCE_SHA256SUMS`. The scorer-only change to `session_map01_v15.py` is also pinned; it does not change the tested input/release code.
- Run `python run_exact_closure.py` with Python 3.11 or compatible from this directory inside a repository checkout. The scripts derive the checkout root from their location. If the evidence directory is outside the checkout, set `ISSUE59_SOURCE_ROOT` to the checkout path. Its raw ordered trace is `raw-exact-closure-01.txt`.
- `ISSUE59_INSERT_INTERKEY_QUERY=1` is modeled inside the harness as an inserted owner `input_state` between the explicit ups; the expected negative control is retained in the same raw file.
- `run_experiment.py` and `raw-run-01.txt` retain the earlier focused wrapper-only baseline. `raw-negative-control-01.txt` retains its independent injected-order negative control.
- `audit_evidence.py` validates result assertions and every file hash in `ARTIFACT_SHA256SUMS`; its output is `AUDIT.txt`.


