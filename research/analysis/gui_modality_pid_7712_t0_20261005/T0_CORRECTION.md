# T0 mutation-control extension

The preregistered mutation suite retained `test_audit.py`, which explicitly changed the source ordering, removed probability mass, and changed a joint-table cell. Its `source/target relabeling` gate therefore exercised the source-name guard but did not separately alter the target name. `audit.py` independently checks the exact target identity, but that branch lacked a direct negative test.

This additive posthoc control adds a target-name mutation against the saved result and reruns only the raw-data auditor tests. It does not rerun the candidate, modify the frozen fixture/output, or rewrite the original 4/4 test outcome. A failure is retained as such; the v2 test file and exact inputs are hash-bound before invocation.
