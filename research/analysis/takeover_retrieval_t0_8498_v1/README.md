# Issue #8498 T0 — low-demand retrieval-practice instrument

Status: `PASS_METHOD` for a deterministic synthetic instrument-validity check only. No participant, live user, real GUI, model, GPU, container, or production data was used.

## H / T / D / C / U

- **H:** On a frozen disposable task family, retrieval practice restricted to predeclared low-demand gaps could improve delayed takeover reconstruction over matched passive restudy without unacceptable distraction. T0 cannot test this human-effect hypothesis; it checks whether a later simulation instrument would leak truth, confound timing, or reward unsafe replay.
- **T:** Generate six truth-table vignettes (verified completion, partial effect, no-effect stop, uncertain delivery, stale focus, held-input/release uncertainty), each represented in PASSIVE_RECEIPT, RETRIEVAL, and NO_PROMPT conditions. Check matched source facts for the first two arms; one common per-case delay chosen independently of treatment; shuffled condition order; predeclared nonurgent gap; unannounced takeover; and scorer rejection of blind replay, repeated last input, and assumed success.
- **D:** `PASS_METHOD` iff the independent auditor reports zero errors on all 18 rows and all five declared corruption tests independently return `FAIL_METHOD`. Otherwise `FAIL_METHOD`. This is construction-method evidence, not human-benefit evidence.
- **C:** A source-bound receipt/checklist may suffice; retrieval prompts can distract; stale GUI state makes verbal recall insufficient; retrieval effects from educational settings may not transfer. The no-prompt arm is a burden comparator, not a safety monitor.
- **U:** Six hand-authored states, one question wording, three ordinal delay buckets, fixed seeds, no participant variability, no real event stream, no model or GUI timing. The low-demand detector itself is assumed, not validated. No conclusion about takeover performance, workload, safety, skill decay, production deployment, or generalization follows.

## Frozen execution and outcome

Candidate: `low_demand_t0_candidate.py`; seeds: condition-order 8498, delay 5849. The delay schedule is generated independently and then copied across conditions within each scenario. Truth and safe next-step expectations are separately encoded in `low_demand_t0_audit.py`; the auditor reads only the generated candidate rows and its frozen truth table.

Executed locally with Python:

```text
python low_demand_t0_candidate.py
=> {"output":"low_demand_t0_candidate.json","rows":18}
python low_demand_t0_audit.py
=> {"audit":"PASS_METHOD","errors":[],"rows":18,"scenario_count":6,"scope":"synthetic instrument validity only","unsafe_replay_policy":"REJECT"}
python low_demand_t0_mutation_check.py
=> all_rejected=true; mismatched facts, answer leak, urgent gap, condition-correlated delay, and blind replay each FAIL_METHOD
```

The mutation suite checks sensitivity to those five declared defects only. It does not prove universal auditor correctness. Raw candidate rows and both audit JSON outputs are retained beside these scripts. Re-run the three commands above from this directory; the scripts have no third-party dependencies.

## Disposition

This scoped T0 may support designing a better-controlled T1 protocol, but it does not authorize participants or a live allocation. T1 still needs independent ethics/consent/privacy approval, preregistration, a separately assigned allocation, a validated low-demand detector, realistic independent task truth, matched restudy/retrieval exposure, and distraction/unsafe-replay outcomes. No original issue result was modified.
