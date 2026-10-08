# W2 `LEASE_CLOSE` ordering probe — host reproduction

Additive diagnostic preregistered in [Issue #5116](https://github.com/Unjuno/agent-interface/issues/5116#issuecomment-5861352348). It does not edit or replace any #5101/#5116 result or frozen source.

## H/T/D/C/U

**H.** For a versioned trace with an exactly bound `LEASE_OPEN` and an input edge after a matching `LEASE_CLOSE`, the frozen W2 verifier and independent raw auditor both fail closed.

**T.** At main `2ac5a00b9879c48f0ecf304c1d3ff01fe4c18ad8`, verify the pinned W2 sources and fixture, make the same versioned `LEASE_OPEN.actuation_id=A4` in control and treatment, then add one matching lease/action close at 50 ns to the treatment. The original input edges start at 100 ns and 400 ns. Run the unchanged verifier CLI and separate raw-auditor CLI on both fresh traces; retain inputs, outputs, exits, and hashes.

**D.** The control must pass both tools. The treatment passes only if both independently reject/hold the post-close input. Verifier acceptance with an auditor close-order rejection is `FAIL_W2_CLOSE_ORDER_CHECKER_DISAGREEMENT`. Missing output or source drift is HOLD/STOP, never PASS.

**C.** The original eight-case fixture is copied in memory and its source bytes remain unchanged. The control and treatment share the one versioned open-binding field; the treatment differs only by the added same-lease/same-actuation close event. Same declared monotonic clock, exact 50 ns close timestamp, synthetic trace only.

**U.** Windows host CPU only, Python 3.12.10. This is a deterministic checker disagreement, not evidence of live unauthorized input, runtime exploitation, GUI/model behavior, or product safety. No Docker/formal execution occurred. Whether missing or foreign `LEASE_CLOSE.actuation_id` invalidates a lease remains a separate contract question.

## Result

`FAIL_W2_CLOSE_ORDER_CHECKER_DISAGREEMENT` (scoped source-checker finding):

- Control: verifier exit 0; `COMPLETED_RELEASE_BEFORE_TERMINAL`, `unauthorized=false`, 298 ns guaranteed / 302 ns possible; independent raw audit exit 0, errors empty, 7/7 existing corruption controls rejected.
- Treatment: the same verifier exit 0 and same authorized disposition/occupancy despite the same `LEASE_CLOSE` at 50 ns preceding both input edges. The independent auditor exits 1 before writing an audit JSON, with `baseline traces fail invariants: ['input_edge_after_lease_close']`.
- Source review explains the disagreement. `verify_contract.py` gathers close times by `lease_id` and uses `bounds[0] <= close_time` as its `expired` predicate; this is false for the post-close edges in the treatment. The raw auditor instead checks `close_time <= bounds[0]` and rejects them. The verifier therefore fails to mark this trace unauthorized, while the independent gate catches it.

The raw source identities and SHA-256s are in `FREEZE.json`. `PUBLIC_RESULT.json` contains sanitized invocation evidence and hashes for every retained trace/report; raw local `PROBE_RESULT.json` remains unchanged. The frozen verifier, auditor, schema, and source fixture are not modified.

## Next gate

Resolve the checker disagreement additively: a candidate must reject edges whose interval begins after a matching close while preserving the pre-close control; an independent raw-only audit must derive the same boundary from event rows. Re-test with the pinned Docker Desktop CPU slot only after an explicit owner transfer and a fresh current-main freeze. Do not merge or promote this host result as formal evidence.
