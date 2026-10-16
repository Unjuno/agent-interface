# Formal stop

Issue #1492 ended with `HOLD_EFFECT_RECEIPT_TOO_SLOW` after exactly one formal invocation.

Candidate current-effect receipt handback closed the visible effect tail in 16/16 positive cases and preserved release/physical-occupancy gates, but case 26 completed 20.341329 ms after actuation-receipt receive. The preregistered bound was max < 8 ms and p95 < 6 ms.

Postformal source inspection found that the frozen waiter passes remaining time to `Queue.get(timeout=...)` but does not re-check the absolute monotonic deadline after wakeup. The formal row is retained unchanged. No rerun is authorized.

A successor must keep the 8 ms deadline fixed and make deadline expiry dominate any receipt returned after that absolute deadline. NO_EFFECT controls already showed receipt0/4 and explicit unresolved timeout4/4.
