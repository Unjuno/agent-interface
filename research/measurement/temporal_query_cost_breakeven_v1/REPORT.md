# #1819 Temporal query-cost break-even surfaces

Decision: **PASS_TEMPORAL_QUERY_COST_BREAKEVEN_SCOPED**

Exact rational enumeration covered all 12,341 denominator-40 priors over RECENT/LONG/EVENT/REVERSAL.

- class-only expected image budget ranges from 2 to 8;
- class+anchor expected image budget ranges from 2 to 4;
- extra image saving from revealing the anchor is exactly `6*p(EVENT)+4*p(REVERSAL)`;
- that extra saving is zero exactly when EVENT and REVERSAL prior mass are both zero.

Therefore, in units of one marginal image cost:
- CLASS_ONLY beats the 11-image universal fixed strategy when class-query overhead is below `11-B_class`;
- CLASS_ANCHOR beats CLASS_ONLY when incremental anchor-query overhead is below `6*p(EVENT)+4*p(REVERSAL)`;
- CLASS_ANCHOR beats UNIVERSAL_FIXED when total anchor-query overhead is below `11-B_anchor`.

For equal priors, thresholds are exactly **6**, **5/2**, and **17/2** image-cost units respectively.

Formal discipline: formal1/reruns0/replacements0/tuning0. Independent audit errors0; all fixed corruption controls reject.

Interpretation: request specificity has value only up to its query overhead. Anchor specificity has no image-budget value when the workload contains only RECENT/LONG relations, and its maximum value is concentrated in EVENT/REVERSAL demand. These are accounting boundaries, not measured token or latency savings.
