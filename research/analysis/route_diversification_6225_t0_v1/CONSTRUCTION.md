# Construction evidence — not the formal T0 result

The candidate contract, schedule semantics and finite cases were exercised on the local Python host before freeze. Construction invocation:

```text
python3 -m json.tool research/analysis/route_diversification_6225_t0_v1/fixture.json
python3 -m unittest discover -s research/analysis/route_diversification_6225_t0_v1 -p 'test_*.py' -v
python3 -m py_compile research/analysis/route_diversification_6225_t0_v1/candidate.py research/analysis/route_diversification_6225_t0_v1/audit.py
```

Current construction pass: 9/9 tests; fixture parses; both modules compile. Tests include a separately written hand-calculated decision table, candidate-versus-independent-enumerator equality on 28 policy/session rows, hidden-shock and counterexample controls, complete-session queue carryover, and nine corruption rejection probes. This is host construction evidence only. The formal candidate and raw-only auditor have not run; no scientific result is claimed.

Earlier in this same construction cycle, successive schedule/fixture drafts failed 2/6, then 3/6, then 2/6 tests. The concrete defects were: the hard-gate survival summary conflated safe unresolved work with severe effects; mixture schedules truncated/omitted offered tasks; expected counts did not match the fixed task sequence; and the oracle misclassified `shock_late`. Those drafts were corrected before the current source freeze. Their outcomes were construction failures, not formal candidate runs; they are disclosed here and are not silently counted as passes.

## Scope of construction

The fixed examples were checked by hand before the final test-table pass:

- hidden A-specific shock: A gets a safe refusal at task 2 and a wrong effect at task 3 before the four-task reactive detector can switch; fixed A/B/B mixture assigns B to both affected tasks and survives;
- observable shock: the context-gated policy sees the shock and avoids the wrong effect, while blind A/B/A/B mixture does not;
- common shock: A and B both cause the severe effect, so mixture cannot rescue;
- stable A-dominant: both routes complete, but B costs more;
- B idle-decay: the third B exposure is unresolved and is charged to the session;
- route-induced queue carryover: B adds three latency units to the next task, making mixture total latency 9 versus 4 for all-A;
- no eligible B: every policy remains on A.

These are intentionally planted finite examples, not estimates. The mixture's one hidden-case win is not an empirical or statistical advantage claim.
