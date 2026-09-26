# #4216 partial asynchronous predicate readiness

Authority-neutral deterministic timing fixture for Issue #4216.

- Construction 01 is retained as a failed fixture: multiprocessing spawn startup polluted the intended evaluation clock.
- Construction 02 changes only the execution fixture to asyncio producers and passes the frozen construction checks.
- Formal allocation is authorized only after these exact source/gate bytes are published and read back.
- READY is evidence only and never grants OS-input authority.

Formal schedule: 6 scenarios × 2 arms × 3 repetitions = 36 cases, one invocation, zero reruns/replacements/tuning.
