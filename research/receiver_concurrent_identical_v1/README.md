# Concurrent identical receiver delivery v1

Direct successor to merged receiver outcome replay evidence. This additive fixture keeps the predecessor `receiver.py` byte-identical and changes only delivery from sequential to two local subprocesses released through a common file barrier.

Formal execution is fixed at 30 cases from `schedule.json`. A third fresh process performs a post-concurrency replay only after both concurrent calls exit. The independent auditor does not import receiver/runner code; it reopens each SQLite database, re-hashes the exact request, checks durable rows, process/event evidence, call overlap, and replay semantics.

Construction: four excluded cases passed before freeze; seven corruption controls were rejected. Formal data must not be pooled with construction.

Scope: local Linux/SQLite process concurrency only. A positive result does not establish distributed exactly-once execution, power-loss behavior, or a production receiver.
