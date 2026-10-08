# W2 binding candidate/auditor CLI — construction extension v3

Issue #5116, additive to the v1/v2 package. The old verifier/auditor finding and prior result files remain unchanged.

## H/T/D/C/U

**H.** A candidate CLI can version binding mutations on an immutable W2 fixture, and a separately launched raw-only auditor can reconstruct every event-row decision without importing candidate code or trusting candidate dispositions.

**T.** Against the exact eight-case source fixture, execute four fresh-output candidate/auditor pairs: unmodified baseline; four versioned matching lease-open bindings; one foreign binding for `release-before-terminal`; and a missing binding for that target. Retain each effective trace, candidate report and auditor report. In unit tests, tamper a candidate disposition and require the raw auditor to reject it.

**D.** Pass the construction gate only if all four raw audits return `PASS_BINDING_RAW_AUDIT_SCOPED`, errors are empty, all 8 case identities reconcile, the four matched targets pass, and foreign/missing target rows fail closed. The mutation-tamper test must produce nonzero auditor exit. Docker/formal acceptance remains separately gated.

**C.** Synthetic records only. The frozen original trace input is hashed and copied in memory before mutation; source fixture bytes are not edited. Candidate and oracle are separate processes/modules. Output roots are fresh. The target foreign/missing mutations affect only the selected LEASE_OPEN actuation binding; three other bound cases remain matched in those runs.

**U.** Host Python 3.12.10 construction only. This checks actuation binding, not lease timing, owner/session, clock conversion, full trace invariants, live authority, GUI effects, task correctness or runtime integration.

## Result

Disposition: `PASS_HOST_CLI_CONSTRUCTION_ONLY`. The complete combined host suite is 15/15 (v1 5/5 retained, v2 6/6 retained, new CLI suite 4/4). Each of the four independently launched raw-audit CLIs returned `PASS_BINDING_RAW_AUDIT_SCOPED` with `errors=[]`.

| Run | Target binding outcome | Raw audit |
|---|---|---|
| Baseline | Original A4/A5/A6/A8 rows HOLD for missing open binding | PASS, 8 cases, 14 reconstructed decision rows (11 input-edge rows plus 3 `NO_INPUT_EDGE` rows) |
| Matched | A4/A5/A6/A8 all match | PASS, 8 cases |
| Foreign | `release-before-terminal`: 2/2 `REJECT_ACTUATION_MISMATCH` | PASS, 8 cases |
| Missing | `release-before-terminal`: 2/2 `HOLD_MISSING_LEASE_ACTUATION` | PASS, 8 cases |

The auditor corruption test changes a candidate row to `AUTHORIZED_MATCH` while raw input still lacks lease actuation; audit exits 1 with `candidate_raw_disagreement:release-before-terminal`.

Exact per-file SHA-256s for all 12 retained raw outputs are in `RESULT_v3.json`; scripts and unit tests are frozen separately. The v3 source snapshot is current-main `2ac5a00b9879c48f0ecf304c1d3ff01fe4c18ad8` with W2 blob identities listed in `FREEZE_v3.json`.

No Docker container was launched. The shared desktop-linux slot remains unassigned; an empty inventory is not an ownership handoff. This output is not formal/container evidence and does not authorize runtime or live input.
