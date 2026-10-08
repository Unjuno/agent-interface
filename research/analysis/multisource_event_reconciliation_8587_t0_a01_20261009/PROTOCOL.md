# Issue #8587 T0 A01 protocol — multi-source event reconciliation

Allocation: `8587-T0-A01-20261009`. This is a finite authored event-trace fixture only. It tests whether a client ledger, toolkit/application log, and OS/window-system projection can localize bounded trace discrepancies without inventing correlations or converting timestamps into causal order. It does not test a real GUI, event completeness, task effect, or action authority.

## H / T / D / C / U

**H:** In the frozen 15-case set, cross-source partial-order reconciliation will localize all eight identifiable seeded boundary faults, exceeding both final-state-only and client-ledger-only controls; it will leave the missing-correlation and truncated-source cases UNKNOWN, accept all five benign controls, and preserve two independent actions as incomparable despite one source's reversed local observation order.

**T:** Candidate input is `model.json` only: 15 deterministic trace projections, source-coverage claims, source-native IDs, the correlation tokens actually present, bounded clock intervals, and explicit action dependencies. The candidate does not read `oracle.json`, which holds the injection key and expected classifications for an independent raw-only audit. Compare final-state-only and client-ledger-only controls with cross-source reconciliation. Each formal executable runs once; the auditor runs only after candidate exit 0 and a nonempty, hash-verified raw file. No model, GUI, network, user, or external effect is involved.

**Fixture:** eight identifiable faults (client duplicate; toolkit omission, duplicate, wrong-window attribution, and generation mismatch; OS duplicate, omission, and delivery beyond the frozen delay bound); two non-identifiable controls (missing propagated correlation token and incomplete OS coverage); five benign controls (clean flow, declared redraw coalescing, reversed observation order of independent events, an independent OS event, and irrelevant redraw).

## Frozen reconciliation contract

The three projection stages are `client → toolkit → os`; source-local IDs are never treated as cross-source IDs. A downstream match is formed only from a non-null `correlation_token` present in both projections. A missing relevant token returns `UNKNOWN_CORRELATION`. Any source whose coverage claim is incomplete returns `UNKNOWN_SOURCE_COVERAGE`; silence in that source cannot establish absence.

A complete-source duplicate token is localized to the source that duplicated it. A missing token at a complete stage is localized to that stage boundary (client-to-toolkit or toolkit-to-OS). A window/generation mismatch is localized to the stage where it first appears. A delay is localized only when the same propagated token and clock domain identify the event pair and the minimum interval gap exceeds the frozen 5 ms limit. `redraw` and `independent` records are declared non-action semantics and are not forced into action-token matching.

Causal edges between projection records require an actually shared correlation token and adjacent declared stages. Action-order edges require an explicit `depends_on` relation. Distinct declared actions with no dependency path are reported as incomparable; source-local sequence numbers and overlapping/non-overlapping clock intervals never fabricate a cross-source action ID or causal edge. Clock intervals are used only for the declared delay bound.

Controls: `FINAL_STATE_ONLY` signals only unequal final-state projections. `CLIENT_LEDGER_ONLY` signals duplicate correlation tokens visible within the client ledger. Neither control receives toolkit/OS logs for classification.

## PASS gate

`PASS_METHOD_SCOPED` requires candidate and auditor exit 0 with exactly one invocation each and zero retries; byte-bound model/oracle/source hashes; exact agreement between every candidate case row and the independent reconstruction; all eight identifiable faults localized to their frozen boundary; both unknown controls remaining UNKNOWN; zero false localizations on benign controls; cross-source localized count strictly greater than both weak comparator counts; the concurrent-reorder pair absent from causal order and present as incomparable; and all five frozen corruption probes rejected (missing toolkit source, forged correlation token, incomplete-coverage mutation, invented event edge, and false localization on a benign control). Any failed condition is retained as `FAIL_METHOD`, `HOLD_AUDIT`, or `STOP`; there is no rerun.

## Execution and scope limits

Freeze current `main`, exact Python/runtime, fixture-builder, model, oracle, candidate, auditor, tests and protocol before formal execution. Formal commands:

```text
python3 -B candidate.py model.json FREEZE.json
python3 -B auditor.py model.json oracle.json FREEZE.json results/candidate.raw.json
```

The finite trace enumerator uses only the Python standard library and does not need a container or shared runtime. A method PASS validates only this authored event model and its declared coverage assumptions. It cannot prove that DOM, accessibility, toolkit, or OS sources are independent or complete; infer semantic application effects; establish race timing or task success; or authorize a live action.
