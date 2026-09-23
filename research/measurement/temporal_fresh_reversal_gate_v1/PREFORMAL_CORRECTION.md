# Pre-primary correction

Primary/formal invocations remained 0. During mandatory self-audit after the first remote source freeze, Python bool/int equality exposed one source bug: `True in {-1,1}` is true, so the A1 candidate could accept boolean fresh direction as +1 while the independently written oracle correctly rejected booleans.

Correction changes only input type validation in `model.py` to require `type(value) is int`, and adds explicit boolean controls to excluded `construction.py`. Scientific direction rule, corpus, seed, parents, D gates, runner, oracle, auditor and corruption controls are unchanged. A1 freeze is retained as `FREEZE_A1_PREPRIMARY.json`; no primary rows exist under A1. The corrected source is re-frozen before the only primary invocation.
