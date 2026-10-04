# Sources and boundary

Existing policy: peer #6915, fixed head b0a4ada9bd41e74d4e6ea059c483ccb672cf917e, `research/concurrency/owned_pipe_cancel_6501_20261003_01a0ff52/candidate.py` and PLAN. Its control-priority branch is the strongest simple comparison and explicitly excludes simultaneous-ready/portable-backend claims. Only the semantic policy is used; no peer producer/auditor/guest was run.

[Python 3.12 selectors documentation](https://docs.python.org/3.12/library/selectors.html) describes readiness keys, nonpositive timeout and Unix pipe support. Actual selected backend is locally verified KqueueSelector/Python3.12.13, not inferred from other-OS documentation. Native ordering is measured once. Full interpreter/kernel/transitive dependencies are not pinned.

Evidence intake includes current #6501 timeline, all-state targeted co-ready/simultaneous pipe PR searches and current base/tree; searches are bounded. No new mechanism/novelty or broad production/adoption claim. Scripts are authored stdlib research retained as inert text.
