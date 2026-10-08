# Capability snapshot XTEST revocation R1

Issue #1927. Parents #1910/#1919; umbrella #40.

H: a runtime-owned capability snapshot minted from actual read-only XTEST discovery is valid only in its exact current surface/generation/content epoch. After a real Xvfb capability-epoch restart from XTEST-enabled to XTEST-disabled, the old snapshot must select no capability; a fresh disabled snapshot may select the declared same-obligation CORE_INPUT_FALLBACK, still with authority=false. Wrong-surface reuse must fail closed.

T: private Xvfb/Tk/python-xlib only. Per epoch pair: start default Xvfb E, QueryExtension(XTEST)=present, mint generation g surface-A snapshot; evaluate fresh-A direct and wrong-scope-B. Kill E and verify process exit/socket disappearance. Restart same display with -extension XTEST as D, QueryExtension absent, generation g+1; evaluate stale E snapshot, fresh D fallback and D wrong-scope. Candidate path performs read-only queries/resolution only; no XTEST/input execution. Construction2 pairs=10 rows; formal16 pairs=80 rows.

D: all lifecycle/capability discriminators pass; E direct16, D stale selections0, D fallback16, wrong-scope selections0/32, candidate/oracle mismatch0/80, authority/input calls0, focus/capability unchanged by each resolver row, source/result/audit integrity PASS, formal1/reruns0.

C: Xvfb restart is a controlled backend epoch, not in-process extension revocation. Generation advancement is harness-owned. CORE_INPUT_FALLBACK is a declared candidate path only and is never executed.

U: private-X11 composition only; no task input/model/token/task-success/latency/general-GUI/runtime-promotion claim.

## Retained preformal fixture-lifecycle stop
The first construction process terminated before CONSTRUCTION.json publication with a Tk/Xlib XIO fatal error when the parent process itself owned the Tk display connection across an Xvfb E->D restart. formal0. Repair changed only lifecycle packaging: Tk A/B remain the same fixture semantics but run in a dedicated child process that is terminated/waited before Xvfb termination/socket-disappearance verification. Scientific scenarios/generations/gates are unchanged.
