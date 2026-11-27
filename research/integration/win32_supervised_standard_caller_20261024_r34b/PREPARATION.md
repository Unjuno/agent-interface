# R34 preparation and custody

R34 is a fresh one-shot successor to R33 on the exact current main commit pinned in `conditions.json`. Its preregistered changes address two concrete R33 misses: at least 21 same-call status polls inside the 1250 ms hold, and an explicit wait for a second injected Q-up hook callback after the held callback returns. No runtime code is changed.

Before any native input, the input-free preflight verifies the clean source commit, all packet and runtime hashes, immutable R33 raw/audit/trace hashes and failure semantics, read-only hook-timeout registry state, and instrumentation self-test. The live run requires an independent same-generation Q-down=true baseline before one cancel. It uses one fixture, one dispatch, at most one cancel, no replay/retry, bounded callback release, and foreground restoration. Any preflight or baseline mismatch stops before the next input and remains FAIL_OR_UNKNOWN.

The fixture click/save happens before the cancellation point. It is only an independent task-effect readback; runtime task_success stays null.
