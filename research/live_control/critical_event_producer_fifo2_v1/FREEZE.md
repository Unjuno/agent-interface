# Source-first freeze

Task `CRITICAL-EVENT-PRODUCER-FIFO2-20260917-001`.
Immutable publication BASE `9717e430b149f943548496e7c1e10ff3cd9c3e32`.
Formal allocation `critical-event-producer-fifo2-20260917-a1`.

Formal cases before this freeze: **0**.
Construction IDs use only `c*`/`c2-*` and are excluded.

One factor: durable producer pending capacity/order policy (`single` capacity1 versus ordered `fifo2` capacity2). Consumer capacity, event identity, ACK semantics, SQLite durability and SIGKILL/restart mechanics remain fixed.

Formal: six first outcomes in `plan.json`, one `run_block.py` invocation, no same-ID rerun/replacement/extension/tuning.
