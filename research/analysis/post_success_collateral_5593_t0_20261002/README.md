# Post-success collateral T0

Synthetic event-ledger method check for the unverified scope extension in Issue #5593. It retains the original first-terminal result and adds two bounded follow-up horizons.

Formal container commands (source is mounted read-only; `/out` is the only writable mount):

```sh
python /work/runner.py --input /work/fixture.json --output /out/candidate_result.json
python /work/independent_audit.py --input /work/fixture.json --candidate /out/candidate_result.json --output /out/audit_result.json
```

Candidate and auditor are distinct processes. `NO_COLLATERAL_COMPLETE` is only a bounded statement to the specified cutoff. `FOLLOWUP_UNKNOWN` and `FOLLOWUP_PENDING` stay inside all-launched upper bounds and outside lower bounds. The exact T0 scope and promotion limits are in `PLAN.md`.
