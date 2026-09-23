# Golden v3 to CLI live Chromium adapter successor v2 (#2337)

Status: PREREGISTERED / no live allocation

This successor corrects PR #2375's fixture pinning error. Historical PR #2375 and all retained evidence remain unchanged.

## H — hypothesis

The current golden-v3-to-CLI boundary can wrap the retained Chromium v5 route without dropping observation identity, lifecycle order, safe-yield progress, independent effect status, or verified release.

## T — frozen comparison

Use the exact retained v5 lineage:

- control runner: `research/live_control/run_compiled_gui_interface_live_v5.py`
- control preregistration: `research/live_control/preregister_compiled_gui_interface_live_v5.py`
- retained result: `research/live_control/results/compiled-gui-interface-live-05/`
- retained source/result hashes are read from `results/compiled-gui-interface-live-05/preregistration.json`

Run one fresh bounded block on the same disposable Chromium fixture:

1. `V5_CONTROL`: retained successful positive/changed semantics.
2. `LIVE_GOLDEN_TO_CLI_ADAPTER`: same task allocation through `runtime/cli_v1/golden_v3.py`.
3. `UNKNOWN_LIFECYCLE`: injected unknown event must fail closed.
4. `UNCERTAIN_DELIVERY`: ambiguous delivery must not replay Submit.
5. `CLEANUP_FAILURE`: cleanup/result status remains distinct from task success.

The changed case must retain `unknown_state`, `completed_actions=1`, `confirmed_partial`, zero Submit input, and independent scorer=false. Every action requires fresh admission and verified release.

## D — data and acceptance

Retain exact source blobs for the v5 runner, adapter/API, lifecycle events, frame hashes, model attempts and usage, dispatch/refusal/repair/delivery status, effect score, cleanup, release receipts, and setup cost.

PASS only if the live adapter preserves field/order/source identity and independently scored effects for positive and changed cases, while all controls fail closed and process completion remains distinct from task success.

HOLD if provider/model usage, GUI/effect evidence, setup cost, or an independent scorer is unavailable. FAIL on dropped lifecycle fields, process-exit task success, unsafe replay, or cleanup reported as task success.

## C / U

This is one Linux/X11 Chromium fixture and one retained v5 lineage. It does not claim generality, token savings, human tempo, second-domain transfer, or production readiness. No live allocation occurs until this preregistration is reviewed and the exact v5 paths/hashes are verified. Historical results are immutable.
