# Disturbance–response feasibility T1

Issue: [#5771](https://github.com/Unjuno/agent-interface/issues/5771)

This finite synthetic construction tests whether a feasibility ledger distinguishes observation alias, missing response, authority gaps, and deadline gaps. See [PLAN.md](PLAN.md) for H/T/D/C/U and scope. `fixture.json` is the constructed finite world; `candidate.py` serializes the ledger; `audit.py` independently reconstructs it; `test_t1.py` tests expected distinctions and dropped-denominator rejection.

Nothing here establishes real GUI disturbance coverage, production safety, or any Ashby-derived quantitative law. Formal container outcome and raw evidence will be added after the preregistered one-shot run.
