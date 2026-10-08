# #1839 first offline contract result

**Disposition: `PASS_MAP01_TASK_EFFECT_CONTRACT_SCOPED`**\
Allocation: `MAP01-TASK-EFFECT-CONTRACT-1839-20260928-01`\
Main/source pin: `2ac5a00b9879c48f0ecf304c1d3ff01fe4c18ad8`

## H / T / D / C / U

**H.** Physical actuation, public state feedback, and independent plan-bound
task effect can be represented as distinct evidence roles on an attested common
monotonic axis without granting input/task authority.

**T.** The current-main source map is frozen in `SOURCE_MAP.md`. After the
13-row corpus, candidate, independent oracle, raw auditor and tests were
hash-pinned in `FREEZE.json`, `run.py` executed once. `audit.py` then consumed
the retained raw `result.json` once; it imports neither candidate nor oracle.
Five focused unittest methods ran before freeze and again after freeze.

**D.** Candidate/oracle mismatches **0/13**; frozen expected-gate mismatches
**0/13**; independent raw-audit errors **0**. One exact-lineage independently
scored synthetic effect is accepted only after the physical DOWN upper bound.
State-only evidence and all 10 hostile corpus rows remain non-TASK_EFFECT.
The five unittest methods also exercise multiple field mutations including
duplicate effect identity. Both authority flags remain false. No live
allocation or external call occurred.

Result SHA-256:
`e26d8808d4238616f3868a48e628931a7c5e253dcc9664dfbfda6da77880be7e`\
Independent audit SHA-256:
`bd561cd6c0ae8837c41186fb97f423e57cb36d284cc1f252aa8c11ca2e3033c4`

Commands, from repository root:

```sh
python3 -m unittest discover -s research/doom/map01_task_effect_contract_1839_v1 -p 'test_*.py' -v
python3 research/doom/map01_task_effect_contract_1839_v1/run.py
python3 research/doom/map01_task_effect_contract_1839_v1/audit.py
```

**C.** The raw records are synthetic contract inputs, not live physical edges.
The accepted composition demonstrates referential/time-bound contract
behavior, not causality. The scorer remains independent and controller-
invisible; state feedback is non-authoritative. No cross-process clock
calibration was performed.

**U.** No claim about actual OS occupancy, normal key-up precision, live
instrumentation availability, effect causality, MAP01 control/survival/clear,
runtime efficacy, model usage, efficiency, or product readiness. Old v38/v39
remain missing-endpoint controls; their run-level totals and HUD transitions
were not promoted. Any live use still requires a separate lease and a fresh
allocation. This result only closes the initial offline contract/readiness
rung in #1839.
