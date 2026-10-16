# Auditor v1 disposition

The one-shot A02 candidate exited 0. The first saved-record audit is preserved verbatim as `AUDIT_V1.*`. It failed only because its predicate required `delivery_unknown.error` to contain both `type` and `message`; the exact frozen ExecutorV12 implementation emits `{"type":"RuntimeError"}` by contract. The V1 audit did not mutate or rerun the candidate.

`audit_v2.py` checks the exact typed shape observed in both executor cells and retains the same three negative controls. Its output is separate (`AUDIT_V2.*`) so the original auditor STOP remains intact. This correction changes only interpretation of the saved result; no candidate input or source snapshot changed.
