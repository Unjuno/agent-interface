# Issue #57 Calc/G10 adapter seam matrix (2026-11-15)

## Scope and source identity

This is an offline composition check against main `dedafadfca1f1322dc8d2fcab5f5049e6681350c`. It joins the retained G10 Calc graph to the current shared guarded X11 bridge, v3 caller, and durable allocation ledger using Fake X transport and deterministic model/effect callbacks. It does not rerun G10, the original actor/auditor, a live Calc session, or a model provider.

Existing contracts are documented in [`calc_g10_current_main_crosswalk_20261027.md`](calc_g10_current_main_crosswalk_20261027.md) and the retained package at [`calc_current_shared_3311_4d74_20261004`](calc_current_shared_3311_4d74_20261004/README.md). The new composed regression is `test_positive_fake_x_path_persists_g10_receipt_before_independent_effect` plus `test_unknown_effect_persists_partial_g10_receipt_without_success_or_outer_score` in [`test_calc_g10_native_caller_composition_v1.py`](test_calc_g10_native_caller_composition_v1.py).

## Requirement-to-existing-test crosswalk

| Requirement | Current enforcement point | Current-main evidence | What this evidence does not establish |
|---|---|---|---|
| #52 typed outcomes and stop before further action | G10 tri-state effect predicate; shared compiled graph and caller receipt mapping | `test_calc_g10_tristate_composition_v1.py` covers match, unavailable, and mismatch; `test_calc_g10_native_caller_composition_v1.py::test_unknown_first_effect_keeps_prefix_and_skips_second_input_and_outer_score` retains one transition and stops | General no-match/ambiguous target behavior across the actual Calc model endpoint is not covered by this G10 fixture |
| #53 all-attempt accounting and retained prefixes | v3 caller plus `run_g10_in_durable_allocation`; hash-linked `DurableCalcAllocation` | New Fake X positive/unknown tests record two synthetic model attempts, usage/cost, compiled receipt, effect receipt or unknown stop, and audited terminal result; `test_calc_durable_allocation_v1.py` separately covers failed model attempt usage and ledger integrity | Model responses, usage, and cost are deterministic fixtures; provider behavior and real usage are not measured |
| #54 schema preflight before GUI authority | No G10-specific live conversion/endpoint path is bound by this composition test | `calc_model_plan_adapter_v1.py` has strict data-only shape checks for a separate R93 task | No endpoint-compatible schema preflight or acquisition-time accounting is exercised in G10 |
| #55 target identity after model wait | fresh proposal, capture digest/sequence/scope, `TargetHandleStore`, guarded admission | `test_calc_g10_fresh_admission_v1.py` rejects wrong digest, changed binding, cancellation, stale alias and timeout; native composition observes old alias `MISSING`, uses a distinct second alias, and asserts capture timestamp follows action return | Provider latency is synthetic; the model-wait-to-input association is not qualified on live Calc or under real modal/external changes |
| Lease, cancellation, release, bounded progress | Shared guarded `_Adapter`, X11 session, bounded proposal worker | Native composition retains verified-empty releases; late proposal and unknown effect stop before a second input; the X transport and application state are Fake X | No native X server/Calc run, OS-level release proof, persistent-input recovery, or collateral-effect measure |
| Independent task effect and evidence | Outer v3 effect verifier after compiled receipt publication | Positive/negative caller-score tests apply the retained saved-XML scorer; new durable case verifies the compiled receipt exists before outer scoring | The saved workbook predates the simulated edits and the new outer effect callback is synthetic; neither proves causation or fresh live success |
| #12/#46 comparison integrity and economics | Durable attempt/result ledger plus frozen comparison plan | The ledger preserves attempts and their reported usage, cost, visible images, and wait; G10 source/capture artifacts remain hash-pinned | There is no matched plain/optimized/integrated block, no cold/warm/invalidation/repair lifecycle comparison, and no live-provider or monetary estimate |

## Added integration result

The positive case runs the full Fake X composition through cold-route caller accounting, the G10 graph adapter, bounded fresh proposal, actual current `NativeHandleBridge`/shared guarded X11 adapter, durable ledger, compiled receipt publication, and synthetic independent effect callback. Its two model-call rows each report fixture usage of 120 input tokens, 20 cached-input subset tokens, 12 output tokens, 4 reasoning-output subset tokens, one visible image, a fixture cost of 0.01, and a fixture wait of 50 ns. The auditor recomputes two attempts, 240 input tokens, 40 cached-input subset tokens, 24 output tokens, 8 reasoning-output subset tokens, two visible images, 100 ns wait, full two-attempt cost coverage, and 0.02 fixture cost. Cached/reasoning token dimensions remain subsets and are not added again.

The unknown-effect companion retains one completed transition and its compiled receipt, produces no outer effect receipt, records no task success, and audits as `EXECUTION_INCOMPLETE`. Both cases assert all Fake X button state is up at return. These fixture numbers are not benchmark measurements.

## Verification

All nine `test_calc_g10*.py` integration modules passed **32/32** in normal mode and **32/32** under `-O**. The durable allocation module passed **8/8** in normal mode and **8/8** under `-O**. `git diff --check` passed.

- G10 normal log: `D:\CodexData\Workspaces\2026-11-15-agent-interface-followup\calc-g10-durable-fakex-20261115-rerun.normal.log` — SHA-256 `DF4C9E4F348C0B6C5A60C17786CA1E0FD9AC66258682892C655C52D45D4D8465`
- G10 optimized log: `D:\CodexData\Workspaces\2026-11-15-agent-interface-followup\calc-g10-durable-fakex-20261115-rerun.optimized.log` — SHA-256 `5B9514C6B7677C068E29F3F2FCA85C4257761EB21FBBAF2D08C9A32F33A7AE2F`
- Durable allocation normal log: `D:\CodexData\Workspaces\2026-11-15-agent-interface-followup\calc-durable-allocation-20261115.normal.log` — SHA-256 `B251F809735AE66B135397FA3FAAFBA18CE74C47C015649D449B948D1ACE2CED`
- Durable allocation optimized log: `D:\CodexData\Workspaces\2026-11-15-agent-interface-followup\calc-durable-allocation-20261115.optimized.log` — SHA-256 `21E7123A86EF8523E9F1944840A6B3BF35D55776A2CF8C6D4A0520944B1A0613`

## Next gate

The concrete offline seam—G10 caller + current guarded bridge + durable accounting—is now covered. The remaining #57 decision requires a prospectively frozen, same-model live Calc lifecycle comparison with cold acquisition, warm reuse, invalidation/repair, every attempt and failure, comparable task effects/releases, and independent scoring. Do not promote Fake X/model/effect receipts as live or economic evidence. Separately, the active R269 Win32 custody remains unresolved while Windows Security owns the foreground; no MAP01 recovery attempt was made in this worktree.

**2026-11-16 public stdio follow-up:** `test_mcp_g10_production_stdio` now exercises the registered G10 path through the real CLI entrypoint and MCP stdio client, including pending-launch exact-call retrieval and parent scoring. The synthetic receipt join passes normal/`-O`. The Windows nested-spawn owner took 10.860/11.031 s with a test-only 20 s wait; the initial production-default 5 s attempt timed out before launch or input. This is not a Linux startup measurement and does not close #57; preserve the timing boundary in the [report](issue57_g10_production_stdio_20261116/REPORT.md).
