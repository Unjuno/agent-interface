# Issue #57 Calc evidence and composition boundary — 2026-11-23

## Scope and source pins

Read-only crosswalk of the retained Calc G10 record, the current comparison
contract, and the existing Calc caller/durable-allocation seam. Current worktree
HEAD is `f8b17b79dbd030774d27e42b0d178c5f44100238`, based on main
`490d7bcb4d84927116112e5ff348cdeadfc489d6`. The historical G10 schema audit
ran at main `ce6449f38a56e1731f01d1024837fb34c9c759a3`; its report and raw
manifest are tracked in Git but omitted from this worktree by sparse-checkout.
They were read from the pinned Git tree, not treated as missing files.

## Evidence crosswalk

| Layer | Existing evidence | What it establishes | Remaining boundary |
| --- | --- | --- | --- |
| Historical live effect | G10 retained `AUDIT.json` and run manifest: two guarded native programs, 11 compiled graph events, three image observations, seven local OCR attempts, and two independently scored saved effects. | A narrow fixed-Calc OCR/compiled-graph positive control; elapsed local OCR time was 493,806,119 ns. | Primary provider/model usage is UNKNOWN; no matched comparison identity or complete caller event ledger. Never convert UNKNOWN to zero. |
| Current comparison admission | The G10 current-main schema audit rejected the unmodified G10 `raw.json` because its caller receipt does not match the reconciled recorder schema; all 33 declared source hashes and 69 retained run files matched in that audit. | The historical effect evidence remains useful while the record is ineligible as a matched efficiency arm. | Do not retrofit absent provider attempts, calls, or usage into G10. The audit was scoped to its pinned 2026-11-21 main and was not rerun against this later main. |
| Current research composition | `research/live_control/calc_g10_caller_v1.py` composes the adaptive caller with the guarded G10 adapter. `run_g10_in_durable_allocation` persists caller events, model-attempt usage, graph binding, execution receipt, effect receipt, terminal result, and abort state. | A plausible new-run evidence path exists; `research/live_control/CALC_DURABLE_ALLOCATION_V1.md` and `test_calc_durable_allocation_v1.py` cover offline ordering, usage, timeout, interruption, torn-log, and tamper cases with the native adapter replaced. | Injected caller/provider/native callbacks remain caller responsibilities. Offline composition tests do not prove production provider completeness, live Calc operation, independent custody, or efficiency. |
| Public runtime model-plan adapter | `runtime/guarded_x11_v1/calc_model_plan_adapter_v1.py` checks a narrow fixed plan and returns preregistered A1/A2 values. | Fail-closed shape checks and fixed task-data translation. | It is not OCR, semantic cell recognition, provider accounting, or a caller-to-effect join. Do not present it as a general Calc adapter. |
| Historical #57 three-arm block | Frozen `integrated-efficiency-live-01` source commit `54910c6f9f0594c609f1f3c6895a918caa64130f` retained 6/6 exact tasks in each plain/ephemeral/persistent arm, 17 model calls including three preflights, all-attempt usage, and task-2 input-token break-even. Persistent elapsed was 44.131 s versus 56.412 s plain (-21.8%) and 73.238 s ephemeral (-39.7%); input tokens were 26,563 versus 63,128/63,779 (-57.9%/-58.4%). A read-only check confirmed all 29 preregistered source hashes against exact blobs from the frozen source commit. | Positive, one-allocation three-arm result under its frozen source and task contract. | This is an older source pin, not a current-main rerun or repeated/population estimate. The checked-in `.source` mirror has three content mismatches (`durable_submit_v4.py`, `received_continuation_v1.py`, `received_exchange_v2.py`) after line-ending normalization; the exact source blobs remain recoverable from the pinned Git commit, so preserve the discrepancy as a custody issue. Current-main standard-caller/provider integration and recovery reliability remain open. See the [frozen preregistration](../../research/live_control/results/integrated-efficiency-live-01/preregistration.json), [report](../../research/live_control/results/integrated-efficiency-live-01/report.json), [audit](../../research/live_control/results/integrated-efficiency-live-01/audit.json), and [source manifest](../../research/live_control/results/integrated-efficiency-live-01-frozen-source-v1/SOURCE_MANIFEST.json). |
| Adjacent desktop comparison | The retained Golden Desktop v1/v3 same-seed pair reports six exact tasks in each run, with v3 9.745 s (20.53%) lower six-task elapsed time and 1,361 (5.13%) more input tokens. | A useful descriptive one-pair App Server/CLI-route result. | Sequential, non-randomized, distinct transport; it does not compare the Agent Interface supervised standard caller or establish a causal efficiency effect. See [v3 report and pair audit](../../runtime/GOLDEN_DESKTOP_DEMO_V3.md). |

## Decision and next gate

No duplicate G10 run or old-record retrofit is warranted. The missing link is
prospective: bind the real provider/model attempt stream and all usage outcomes
to the durable public-caller allocation for every arm, then bind the saved-byte
score, release/recovery, and latency endpoints to the same attempt identity.
The durable allocation seam is a starting point, not proof that those live
bindings already exist.

Before a new matched run, audit the production caller's provider callback and
recording path against the durable writer using failures, timeout/deferred
completion, unknown usage, and score/release ordering. Freeze a finite matched
allocation only after this path can account for every provider attempt. Reuse
the historical G10 task/effect as scoped reference material; do not replay its
consumed allocation. Keep #57 open.

This note is an offline source/evidence crosswalk. It adds no live result, code
change, or new reliability/efficiency claim.
