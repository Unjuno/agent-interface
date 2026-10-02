# Host lease-contract result — T0-01

**Disposition: `FAIL_HARNESS_DEADLINE_SCHEDULE_NOT_ADVANCED`.** The candidate and independent auditor were each invoked once; no retries.

The actual frozen `Lease` source returned `True` for the pre-deadline cancellation case, and the harness labeled that worker cancelled. At the exact deadline, the actual source raised `Expired`, correctly keeping that boundary distinct from a pre-deadline acknowledgement. But the nominal no-cancel case did not advance the synthetic clock from 100 ns to its 1000 ns deadline before calling `wait(0)`. The actual Lease therefore returned `False` and the candidate labeled the worker `continued`. The raw-only auditor rejected that case because the preregistered deadline schedule was not executed.

This is a harness/schedule failure, not a Lease failure and not evidence about #6228's runner timing. The original candidate raw JSONL and failed audit are retained unchanged. No candidate or auditor rerun, repair, Docker action, GUI/model call, or external effect occurred. A corrected schedule would require a fresh allocation and freeze.

The result is construction evidence only. No inference is made about synchronous clock RPC delay, executor timing, MAP01, release latency, safety, or task effect.
