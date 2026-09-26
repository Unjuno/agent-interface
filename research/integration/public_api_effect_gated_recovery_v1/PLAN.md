# Issue #4120 — public API effect-gated recovery v1

Base: `210c92b801f9c73e72a31545f5027675c3bb752c`.
Branch: `research/public-api-effect-gated-recovery-20260922`.
Additive path: `research/integration/public_api_effect_gated_recovery_v1/`.

## H
After public Python API native completion, independent application effect disposition must gate recovery. WRONG_FIELD is collateral and must not be replayed. NO_EFFECT may admit one bounded click-to-focus repair, but a public pixel observation after the click is not a current Tk-recipient certificate. A later current recipient receipt should prevent the directed post-click B-focus error.

## T
Exact current-main public API/X11/core source closure is materialized and Git-object checked before construction. Three policies × three schedules × two fresh repetitions = 18 formal cases, in two immutable nine-case batches. Every case uses a fresh private authenticated, TCP-disabled Xvfb and a fresh ordinary Tk application. All text/pointer task input goes through `dispatch_golden_v3`; the recovery observation goes through public `observe`. Fixture IPC may set focus/query state but never writes task text.

Construction is separate and excluded. Construction-01..04 exposed target/focus setup defects; construction-05 is the first complete nine-cell characterization matching the expected table; construction-06 repeats the same excluded nine cells after self-contained vendoring and is the final pre-freeze construction check. Formal batches are never retried/replaced/pooled.

## Frozen expected table

| policy | schedule | first effect | recovery input | final A | final B | final disposition |
|---|---|---|---:|---|---|---|
| BLIND_RETRY | NO_EFFECT_STABLE | NO_EFFECT | yes | empty | empty | NO_EFFECT |
| BLIND_RETRY | WRONG_FIELD_FIRST | WRONG_FIELD | yes | empty | 77 | WRONG_FIELD |
| BLIND_RETRY | NO_EFFECT_B_AFTER_CLICK | NO_EFFECT | yes | empty | 7 | WRONG_FIELD |
| EFFECT_GATED_CLICK | NO_EFFECT_STABLE | NO_EFFECT | yes | 7 | empty | SUCCESS |
| EFFECT_GATED_CLICK | WRONG_FIELD_FIRST | WRONG_FIELD | no | empty | 7 | WRONG_FIELD |
| EFFECT_GATED_CLICK | NO_EFFECT_B_AFTER_CLICK | NO_EFFECT | yes | empty | 7 | WRONG_FIELD |
| RECIPIENT_GATED_CLICK | NO_EFFECT_STABLE | NO_EFFECT | yes | 7 | empty | SUCCESS |
| RECIPIENT_GATED_CLICK | WRONG_FIELD_FIRST | WRONG_FIELD | no | empty | 7 | WRONG_FIELD |
| RECIPIENT_GATED_CLICK | NO_EFFECT_B_AFTER_CLICK | NO_EFFECT | no | empty | empty | NO_EFFECT |

## D
`PASS_EFFECT_GATED_RECOVERY_BOUNDARY_SCOPED` requires exactly all 18 cells and both batch exits; current-main source hashes; every native program completed with verified empty release; public observation no-authority/no-input; no `task_success=true` inferred from program completion; effect-gated stops WRONG_FIELD and succeeds stable NO_EFFECT but exposes its post-click focus-change weakness; recipient-gated additionally refuses current B before retry. Raw-only audit errors must be zero and all 12 corruption controls must reject.

Any recipient-gated recovery input with a current B receipt is `FAIL_RECOVERY_RECIPIENT_GATE`. Missing source/process/effect/release evidence is STOP/HOLD.

## C
The recipient receipt is cooperative application evidence, not a generic runtime API or authentication. Exact geometry is fixture-supplied. Barrier-directed focus changes are counterexamples, not natural race-rate estimates. Program completion and task effect remain separate.

## U
No model/provider, token/latency benefit, MCP/CLI parity, arbitrary toolkit, cross-platform, natural failure rate, automatic rollback, six-task matched efficiency or product/integration-spine PASS.

## Formal commands

```sh
PYTHONPATH=vendor python run_matrix.py --out formal/batch-0 --rep 0 --display-base 240
PYTHONPATH=vendor python run_matrix.py --out formal/batch-1 --rep 1 --display-base 260
PYTHONPATH=vendor python audit.py formal --freeze FREEZE.json --controls --out AUDIT.json
```
