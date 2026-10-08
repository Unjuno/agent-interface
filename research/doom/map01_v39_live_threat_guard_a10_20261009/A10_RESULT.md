# A10 live result

Allocation `map01-v39-live-threat-guard-a10-20261009` ran once on exact current main `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`, with experiment tree `5c6dc5451bf52aa0cc0b33b00ee4603715673da5`. The exact raw output, `FREEZE.json`, and first `AUDIT.json` remain local and immutable; A10 was not retried.

The one-shot run stopped after 62.396 seconds at 13 completed model turns. The game ended with one kill, one death, and no MAP01 exit. The controller refused a source refresh on invalid observed health and exited 1. The app-server exited 0, forwarded 17 requests and 1,907 responses, and reported no relay error.

The frozen original audit is **FAIL**. The additive cancellation reconciliation is **STOP**: 13/13 cancellations are accounted for under admission-aware custody (3 active-input cancellations have matching token-bound releases; 10 no-input cancellations have verified-empty terminal receipts). The original audit FAIL remains preserved. The controller failure receipt reported an overly broad cleanup failure despite complete terminal receipts; a targeted lease-aware fix is in PR #8763.

The live gate was not met: zero hard-health guard exposures and zero useful scorer events during pending inference; one useful scorer event occurred outside pending inference. A10 is **STOP**, not efficacy or task completion.

## Public copy and evidence scope

`A10_AUDIT_PUBLIC.json` contains aggregate checks and counts only. It omits raw intent tokens, per-key identities, session/turn identifiers, and local paths. `A10_FREEZE_PUBLIC.json` redacts host paths and the public commit reference that exposed one. Exact execution freeze, runner, first audit, and the raw allocation manifest remain local. The public runner and auditor derive and validate the host mount root from the nested checkout; this path-only publication sanitization was made after execution. Their SHAs therefore differ from the exact executed copies recorded in the local freeze. No experiment was rerun and the public copy is not represented as byte-identical execution source.

One episode is descriptive. It cannot estimate an effect rate, establish a survival benefit, or demonstrate MAP01 completion. X11 receipts establish server-side event processing and observed server state, not hardware key state or game consumption.
