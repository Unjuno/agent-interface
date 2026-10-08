# Result — #5156 release receipt compatibility construction

Allocation `MAP01-OWNER-KEYUP-RECEIPT-INTEROP-5156-20260928-01` ran once from the source identities recorded in [`../../FREEZE.json`](../../FREEZE.json).

## Outcome

**`FAIL_RELEASE_RECEIPT_INTEROP`** — 6 of 7 source-supported receipt test vectors were rejected by the merged #5175 validator. The one accepted autonomous reason was `cancelled`.

| Case | Actual owner form | Validator outcome |
|---|---|---|
| `expired` | autonomous InputOwner release | rejected: `autonomous reason missing or unknown` |
| `focus_changed` | autonomous InputOwner release | rejected: `autonomous reason missing or unknown` |
| `stop_requested` | autonomous InputOwner release | rejected: `autonomous reason missing or unknown` |
| `surface_changed` | autonomous InputOwner release | rejected: `autonomous reason missing or unknown` |
| `thread_exit` | autonomous InputOwner release | rejected: `autonomous reason missing or unknown` |
| `cancelled` | autonomous InputOwner release | accepted |
| integer `button_up` (`button: 1`) | transition wrapper + InputOwner v10 | rejected: `key identity missing` |

Pinned Git blobs were checked inside the runner: owner `341b3c01649943ddaad5f28431a792c4889cc36e`, wrapper `0ea631abcf6272f0538a9ef9198ad8069b47b464`, protocol `55272e127073a84c9eb541bc650fee74f3fc7123`. Protocol SHA-256: `3ae2ad7ca09bdd6572080aa55ce9fae9cb24a566629c95bf9736220098f134cd`.

The independent auditor exited 0 with `PASS_EXPECTED_COMPATIBILITY_FAILURES_REPRODUCED`, zero errors, and exactly the six preregistered mismatches. `RESULT.json` SHA-256: `d722609a53fb062d368200106559b37d28ad72f50278ba86495c8d751801838e`; `AUDIT.json` SHA-256: `ee7856cefdc87e9c43fc303314be02fec77fbb1eee446941d26230c95016c4b4`.

## Scope

This is a pure construction/interop failure, not a failure of the X11 runtime or key release. The pinned Docker Desktop run used offline, read-only source mounts and produced no input authority. No InputOwner instance, X11 server, XTest/XSync, GUI, OS input, model/provider, or game ran. No exact key-up or application-consumption timing is claimed. The result does not measure MAP01 occupancy or gameplay efficacy.

## Next gate

Before any #5156 X11 fixture, amend the receipt schema to use the actual owner cause vocabulary and separately type key versus integer button identities; then add positive and negative end-to-end owner/wrapper receipt tests. Preserve the merged #5175 source and this failure as-is. A new current-main freeze and fresh queue assignment remain required before the X11 fixture.
