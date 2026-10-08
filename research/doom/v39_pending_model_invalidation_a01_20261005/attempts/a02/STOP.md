# A02 construction failure

Disposition: FAIL_CONSTRUCTION_HARNESS; no retry under A02.

The candidate imported the current V39 source and entered the pending-model cancellation path, but its post-cancel fake planner result used a hard-coded terminal-observed / decision clock. The actual monitor outcome_evaluated_ns was later than that value, so the production final-admission helper correctly rejected the malformed receipt with ValueError: controller decision precedes observed boundary. No candidate result JSON was produced and the independent audit did not run. Retained stderr SHA-256: 8f8c0e4278519bff8f4337dfbe3a70cc0faf92008ff9a500bcae0a2412a10492.

A03 changes only the harness clock source to monotonic time and records the independent interruption count; source code, signal thresholds, events, and decision rules remain fixed. A03 has a distinct output path and freeze.
