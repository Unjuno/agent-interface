# Unfrozen preparation failure

The predicate test subprocess omitted PYTHONPATH and failed to import runtime. Dependent orchestration mistakenly launched one owner despite that failure, before a FROZEN manifest existed. This is not a comparative case. Original owner handle 36276 was closed once, exit 0, without observation or input; one cleanup-only command and verified neutral close are retained. Owned application processes terminated and were absent at audit.

STOP.json records the error, one startup allocation, zero input/observations and all four unexecuted comparative cases. Successor02 explicitly tests the same launch environment and freezes before allocation. Preserve this preparation cost/failure rather than replacing it with a successful case. There is intentionally no retrospective FROZEN manifest for01.
