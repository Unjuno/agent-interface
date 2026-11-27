# Issue #57 composition experiment R04 result

Frozen base: `844f18ae601e31caa13527c495d4548ebe8f40cb`
Harness commit: `c96f4c2f96f69bf4eaa4f5601bfe2ffd0f398e32`
Interpreter: Python 3.13.14 (Windows AMD64)

## Result

`PASS_SYNTHETIC_COMPOSITION_ONLY`. Both normal and `-O` bundles exited 0. Each included one positive and one changed-intermediate case. The independent auditor verified protocol usage joins and durable-allocation custody in all four cases.

| Mode | Case | Outcome | Actions | Provider attempts | Usage joined | Durable status | Effect receipt |
|---|---|---|---:|---:|---|---|---|
| normal | positive | TASK_SUCCEEDED | 2 | 1 | yes | audited | yes |
| normal | changed-intermediate | EXECUTION_INCOMPLETE | 1 | 1 | yes | audited | no |
| optimized | positive | TASK_SUCCEEDED | 2 | 1 | yes | audited | yes |
| optimized | changed-intermediate | EXECUTION_INCOMPLETE | 1 | 1 | yes | audited | no |

## Execution receipts

- normal: exit `0`, elapsed 0.948s, stdout SHA-256 `9527514de8f434862a5eaf748a89e6aa18d04afe707c6d55d57255b100631bd8`, stderr SHA-256 `49bec1a785698e19381452742494eabd0477e584b1a1c3a46f65c1fd873e8939`.
- optimized: exit `0`, elapsed 0.638s, stdout SHA-256 `9527514de8f434862a5eaf748a89e6aa18d04afe707c6d55d57255b100631bd8`, stderr SHA-256 `bb294dd958395805c3bf6f6b5d59fe25e79a72df84ed29fc3b45ccd0c563b8cf`.

The positive fixture ran `enter_value` then `submit`, recorded verified empty key/button release receipts, and persisted an independent task-effect receipt. The changed-intermediate fixture ran only `enter_value`, returned `EXECUTION_INCOMPLETE / unknown_state / confirmed_partial`, persisted execution custody, and did not call the independent task scorer or persist an effect receipt.

## Interpretation and limits

This closes one offline composition seam in current-main: deterministic App Server usage -> persistent grounding adapter -> v3 caller -> compiled GUI execution -> durable execution/effect custody. It does not establish actual provider integration, GUI control, deadline-expiry stale-input suppression, recovery reliability, matched cost/latency economics, cold-path behavior, runtime packaging, MAP01, or Research Preview graduation. No live allocation was used. R01–R03 preflight failures and the first audit startup failures are preserved under `raw/` and recorded in the R04 conditions revision notes; no failed preflight launched a scenario.

Conditions: [`CONDITIONS-r04.json`](CONDITIONS-r04.json). Independent audit: [`AUDIT.json`](AUDIT.json). Raw and attempt artifacts remain under `raw-r04/` and `attempts-r04/`.
