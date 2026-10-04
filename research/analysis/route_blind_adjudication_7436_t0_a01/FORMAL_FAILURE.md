# A01 formal disposition — FAIL_SETUP_ENTRYPOINT

The frozen candidate invocation was consumed once and exited 1 before candidate logic or output creation:

```text
Traceback (most recent call last):
  File "/private/tmp/agent-interface-7436.ifazsA/repo/research/analysis/route_blind_adjudication_7436_t0_a01/candidate.py", line 6, in <module>
    from presenter import Custodian, make_packets, synthetic_scores
ModuleNotFoundError: No module named 'presenter'
```

Cause: isolated Python `-I` does not add the script directory to `sys.path`. The construction suite imported the module after explicit path insertion, so it did not exercise the frozen CLI entrypoint. Auditor invocations: 0. Candidate outputs: none. Retries: 0. This is an entrypoint/setup failure, not a result about the route-blinding method. A separately frozen successor allocation is required to test a corrected isolated entrypoint; A01 will not be rerun.
