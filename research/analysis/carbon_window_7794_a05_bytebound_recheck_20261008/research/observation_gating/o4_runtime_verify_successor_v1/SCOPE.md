# O4 runtime VERIFY scope

This pure gate evaluates a non-authoritative verifier receipt against current observation identity and intent epoch. TRUE/FALSE may suppress escalation only when exact current binding matches. UNKNOWN, malformed, stale, mismatched, or authority-bearing receipts escalate.

No model, GUI, input, provider, or authority call is made.
