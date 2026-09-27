#2499 ledger contract preflight

This additive contract freezes the minimum ordered ledger shape for a future one-session four-transition allocation. It rejects missing trace, sequence gaps, authority grants during observe-only recovery, and missing cleanup evidence.

It does not execute GUI transitions, admit input, score effects, or establish #2499 acceptance. A future live runner must emit these fields at capture time; post-hoc synthesis is invalid.
