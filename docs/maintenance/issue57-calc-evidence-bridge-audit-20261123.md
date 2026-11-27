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
| App Server to durable-ledger composition R01 | New test uses the real JSONL client/parser and grounding adapter with a synthetic peer, then composes v3 caller → `run_g10_in_durable_allocation` → durable allocation audit. The malformed answer is retained as one failed attempt with exact call/thread/model/settings and all five usage counters; no execution/effect receipt is written. Both tests pass 2/2 normally and under `-O` on Windows Python 3.13.14. | The synthetic provider-error/usage path survives into a locally hash-linked allocation. | No external provider; does not exercise a valid-answer completion in this combined composition or connect `ProspectiveRun`'s three-arm assignments to dispatch. See the [R01 packet](../../research/integration/issue57_v3_durable_appserver_composition_r01_20261123/RESULT.md). |
| Public runtime model-plan adapter | `runtime/guarded_x11_v1/calc_model_plan_adapter_v1.py` checks a narrow fixed plan and returns preregistered A1/A2 values. | Fail-closed shape checks and fixed task-data translation. | It is not OCR, semantic cell recognition, provider accounting, or a caller-to-effect join. Do not present it as a general Calc adapter. |
| Historical #57 three-arm block | Frozen `integrated-efficiency-live-01` source commit `54910c6f9f0594c609f1f3c6895a918caa64130f` retained 6/6 exact tasks in each plain/ephemeral/persistent arm, 17 model calls including three preflights, all-attempt usage, and task-2 input-token break-even. Persistent elapsed was 44.131 s versus 56.412 s plain (-21.8%) and 73.238 s ephemeral (-39.7%); input tokens were 26,563 versus 63,128/63,779 (-57.9%/-58.4%). A read-only check confirmed all 29 preregistered source hashes against exact blobs from the frozen source commit. | Positive, one-allocation three-arm result under its frozen source and task contract. | This is an older source pin, not a current-main rerun or repeated/population estimate. The checked-in `.source` mirror has three content mismatches (`durable_submit_v4.py`, `received_continuation_v1.py`, `received_exchange_v2.py`) after line-ending normalization; the exact source blobs remain recoverable from the pinned Git commit, so preserve the discrepancy as a custody issue. Current-main standard-caller/provider integration and recovery reliability remain open. See the [frozen preregistration](../../research/live_control/results/integrated-efficiency-live-01/preregistration.json), [report](../../research/live_control/results/integrated-efficiency-live-01/report.json), [audit](../../research/live_control/results/integrated-efficiency-live-01/audit.json), and [source manifest](../../research/live_control/results/integrated-efficiency-live-01-frozen-source-v1/SOURCE_MANIFEST.json). |
| Adjacent desktop comparison | The retained Golden Desktop v1/v3 same-seed pair reports six exact tasks in each run, with v3 9.745 s (20.53%) lower six-task elapsed time and 1,361 (5.13%) more input tokens. | A useful descriptive one-pair App Server/CLI-route result. | Sequential, non-randomized, distinct transport; it does not compare the Agent Interface supervised standard caller or establish a causal efficiency effect. See [v3 report and pair audit](../../runtime/GOLDEN_DESKTOP_DEMO_V3.md). |

## Decision and next gate

No duplicate G10 run or old-record retrofit is warranted. The failed-attempt
transport-to-durable-ledger path now has one passing synthetic composition
test. The remaining link is prospective and higher-level: connect valid and
failed real provider/model attempts for all three arms to the durable public
caller allocation, then bind saved-byte score, release/recovery, and latency to
the same attempt identity. `ProspectiveRun` explicitly records
`dispatch_enabled: false` and has no provider/input adapter; the offline R01
does not enable it or prove those live bindings.

Before a new matched run, compose the three-arm `ProspectiveRun` boundary with
the existing v3 provider adapter and durable task custodian on synthetic
success, failure, deferred completion, and unknown-usage cases. Then freeze a
finite live matched allocation only after every provider attempt can be joined
without loss. Reuse the historical G10 task/effect as scoped reference
material; do not replay its consumed allocation. Keep #57 open.

This note is an offline source/evidence crosswalk. It adds no live result, code
change, or new reliability/efficiency claim.

## Current-main R03 success-path follow-up - 2026-11-23

The worktree was checked against origin/main at
2cf4230f918f1b05990a4491779805cc18658e12. A frozen one-task synthetic
success fixture exercises JSONL client/parser, persistent grounding model,
v3 adapter/caller, run_g10_in_durable_allocation, and registered ProspectiveRun
custody. Unlike the earlier success-shaped dictionary stub, provider output
and usage enter through the real JSONL parser. Exact call/thread IDs and five
usage counters survive durable audit; synthetic execution/effect receipts
produce one projected task. The focused test passes 1/1 and the module passes
7/7 in normal and -O on Windows CPython 3.13.14.

This establishes the local success transport seam only. The fake peer is not a
provider, the execution/scorer are synthetic, custody attestation is injected,
and 17 of 18 assignments remain missing with dispatch disabled. It does not
establish real-provider accounting completeness or make a matched live
allocation admissible. See the [R03 packet](../../research/integration/issue57_v3_durable_appserver_composition_r03_20261123/RESULT.md).

## Current-main R04 UNKNOWN-usage follow-up - 2026-11-23

A fake JSONL peer completed with terminal status failed and no usage update.
The actual parser/model/v3 caller/durable writer/ProspectiveRun path retained
the failed attempt's turn/thread identity and left every usage total None.
Custody audited; no execution/effect receipt was recorded; task and run stayed
HOLD with dispatch disabled. Focused 1/1 and the full eight-test module pass
normal and -O on Windows CPython 3.13.14. This confirms UNKNOWN is not turned
into zero in this fixture. It is not live provider evidence or proof that all
provider response shapes are covered. See the [R04 packet](../../research/integration/issue57_v3_durable_appserver_composition_r04_20261123/RESULT.md).

## Current-main R05 successful effect with UNKNOWN usage - 2026-11-23

The valid synthetic App Server answer completed with no usage notification.
The caller retained TASK_SUCCEEDED and its synthetic task effect; durable
custody audited execution and effect receipts. All five provider usage totals
remained None, so the frozen comparison projector held the row with
usage_incomplete_or_invalid. Focused 1/1 and the complete nine-test module
passed normal and -O on Windows CPython 3.13.14. This demonstrates that a
successful effect is retained while incomplete accounting blocks comparison.
It does not establish live-provider usage completeness or efficiency. See the
[R05 packet](../../research/integration/issue57_v3_durable_appserver_composition_r05_20261123/RESULT.md).


## Current-main R06 timeout after observed usage — 2026-11-23

A synthetic JSONL peer emitted usage then timed out without terminal completion.
The actual transport/parser/model/v3 caller/durable writer/registered
ProspectiveRun path retained exact IDs and all five observed usage counters;
no task effect/receipt was created, and projection/run stayed HOLD with 17
assignments missing and dispatch disabled. Focused 1/1 and full module 10/10
passed in normal and -O on Windows CPython 3.13.14. This is an additional
synthetic timeout-custody shape, not proof of external-provider completeness or
matched economics. See [R06 packet](../../research/integration/issue57_v3_durable_appserver_composition_r06_20261123/RESULT.md).
