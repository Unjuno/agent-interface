# Independent audit

The runner enumerates all 3^3 timestamp assignments. Strict coherence is equality of all field timestamps; bounded skew is max-min <= 1. Counts are independently determined: 3 strict cases and 15 bounded cases. Naive latest-per-field accepts 24 mixed-time cases. A preformal construction assertion incorrectly expected 21 bounded cases; this was corrected to the combinatorial union count 8+8-1=15 before the single formal invocation. Formal=1, reruns=0, tuning=0.

Result digest: ea2d83d24dca54c6680d2bdb305dca5bcd9bcb338c4df51b1d890548cfc4f126.
