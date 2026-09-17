# Typed epistemic recovery identity — frozen experiment plan

Issue #881. This is a one-variable successor to #875: distinguish an unrecorded refinement (`UNKNOWN`) from an explicitly observed null (`KNOWN_NULL`) instead of coercing both to a nullable scalar.

H/T/D/C/U are frozen in Issue #881. No model prompt is used. The model-visible/natural-language contract is the Issue text; this runner is deterministic retained-evidence replay only.

Formal inputs are the exact #855 and #864 first-outcome archives. Formal execution is 32 rows (16 sessions × stale/fresh receipt) exactly once after source-first publication/readback. Every result is observation-only.
