# TDD red/green receipt

## Aggregate query failure

Before the owner change, `test_aggregate_keymap_failure_preserves_confirmed_per_key_up_without_neutral_claim` ran against the exact A01 InputOwner Git blob `82d3881dd4064f58e847420bb336a70cd84ee307` with fake-display `query_fail_on={5}`. It failed at the assertion `len(rows) == 1` with `AssertionError: 0 != 1`. The preceding per-key up sample had confirmed F8 neutral, but the aggregate exception occurred before `owner_release` was appended, so the bridge had no row to drain. The original console result was observed in this Codex run; the final GREEN raw event summary is retained in `candidate-suite-final.log`.

After the A02 change, the same test emits `RAW_RESULT` with one F8 `CONFIRMED_PHYSICAL_UP` row, `release_errors=["sample failure"]`, one owner record with `verified=false`, `verification_status=UNAVAILABLE`, `keys_down=null`, `buttons_down=null`, empty `bridge_held`, and empty `fake_physical`. The complete candidate suite log preserves this output.

## Executor final release barrier

The first exact candidate test draft modeled `release_all()` as an `input_state` query. That was not the production owner-release contract, so its failures are preserved as setup diagnostics (`expiry-attempt01-harness-miswire.*`, `expiry-diagnostic.*`). The corrected fixture calls `owner.release` synchronously, consistent with the inherited session backend release path.

With that corrected fixture and the frozen A01 bridge, the test fails as expected: the terminal contains a verified owner release with a confirmed F8 up, but emitted events contain no `input_release_measurement`; `bridge.held` remains `["F8"]`. Raw baseline: `expiry-red-a02-owner.log` (exit 1). With the A02 bridge, the test passes: the single contextual confirmed-up row precedes the expired terminal, and both fake state sets are empty. Raw candidate: `expiry-green-a02.log` (exit 0).

An earlier copy of the focused suite still pointed to the A01 package and is retained as `candidate-suite-attempt01-harness-miswire.*`. It is excluded. The corrected full A02 run is `candidate-suite-final.log` (10/10).
