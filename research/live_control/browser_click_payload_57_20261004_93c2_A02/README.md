# Click-time payload rewrite boundary — first six native cells

Original C03 endpoint/heading guard and the prior A01 private pre-click validity reference both reported `EFFECTIVE_UI_SAVED` in every cell. Independent HTTP truth records:

| Fixture click handler | Intended | Actual POST | Native shape valid | Exact task effect, per arm |
|---|---|---|---|---|
| Identity | GHI | GHI | true | true |
| Valid rewrite | GHI | XYZ | true | false |
| Invalid rewrite + noValidate | GHI | x | false | false |

Three new handler conditions × two arms, serial fresh headless Chromium contexts. Changes occur inside the click handler after pre-click checks, unlike A01 input-handler mutations. All six post-fill snapshots were GHI/valid/no bypass; both reference validation snapshots were also true/no bypass. Complete input/click-before/click-after/submit events and18 HTTP records retained. Six copied semantic contradictions refused. No historical A01/native/peer/formal/model cell replay.

Node61225/native Chromium151.0.7922.34/browser61226 completed six cells and exited0; parent wrappers closed, server closed, known two PIDs absent in later ps read. Independent saved reader61431exit0, empty stderr. Source/definitions fixed before execution and unchanged; outer60s timeout configured, output budgets met by measured bytes (not proved resource enforcement).

**ENVIRONMENT_REPRODUCIBILITY_HOLD:** Node/Playwright/browser binaries and dependencies were not pre-hash-frozen despite the planned requirement. Keep this first source-bound ordinary native observation; no retrospective freeze, strict environment reproducibility PASS or producer rerun. No screenshot/actual OS keyboard/native release/model/efficiency or physical GUI guarantee.

The original C03 narrow destination contract is respected. This fixture is a deliberate app-side payload mutation, not a natural failure-rate/security claim or production defect discovery. Checking format alone excludes x but not valid wrong XYZ; exact intended effect requires an independent value/effect check. Existing semantic-method owners retain adoption. No runtime/default/import/workflow change is included.

DATA ONLY proof: strict gzip→JSON members[].base64; verify each member byte count/SHA before reading. Embedded .py/.js images are retained evidence, not execution entries. Original raw/control/full streams and qualifications are complete. Claim5970773757, sourceowner93c2, parent57/7070. Broad goal active, main sends0.

{
  "members": 33,
  "json_bytes": 303951,
  "json_sha256": "f767ef7d2a6303fc8becccc8aca40c6f0fd97f71699a4938865963ea09fc23a8",
  "gzip_bytes": 39508,
  "gzip_sha256": "1d2e153020954abfcaef20ca12ff792cf5c8706b1c7c34c8c82e044cd4a386e6"
}
