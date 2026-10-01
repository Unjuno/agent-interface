# guard_stale_cost_2494_v1

Retained first outcome for Issue #2494. Do not rerun the consumed formal batches to fill the missing denominator. Restore the exact archive with `python -B unpack.py /tmp/guard2494` and run `python -B /tmp/guard2494/study/audit.py /tmp/guard2494/audit_input`; the expected exit is nonzero with exactly the retained incomplete-denominator errors. The HOLD is intentional.
