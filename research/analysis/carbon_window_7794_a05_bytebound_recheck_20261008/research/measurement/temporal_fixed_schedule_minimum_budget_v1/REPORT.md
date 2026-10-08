# #1640 Minimum universal fixed temporal budget

Decision: **PASS_TEMPORAL_FIXED_SCHEDULE_MIN_BUDGET_11_SCOPED**

## Lower bound

RECENT_DENSE requires four distinct samples in [900,1000]. Seven additional frozen request constraints require at least one sample in each of these pairwise-disjoint regions:

- REV_L(300): [150,275]
- EVENT_R(275): (275,375]
- EVENT_R(375): (375,475]
- EVENT_R(475): (475,575]
- EVENT_R(575): (575,675]
- EVENT_R(675): (675,775]
- EVENT_R(775): (775,875]

These seven regions are mutually disjoint and also disjoint from [900,1000]. Therefore every universal fixed schedule needs at least 4+7=11 timestamps.

## Upper bound

The 11-point schedule `(225, 325, 425, 500, 600, 700, 800, 900, 925, 950, 975)` satisfies RECENT_DENSE, LONG_BASELINE, all 24 EVENT_CENTERED anchors, and all 24 REVERSAL_BRACKET anchors on the complete 25-ms grid.

Thus the minimum universal fixed budget is exactly 11.

Interpretation: under this frozen relation family, a four-image query-conditioned policy can cover every later-revealed relation while a universal fixed policy needs at least 11 images to remove that structural coverage disadvantage. This is an information-allocation theorem only, not evidence that a model performs better or that query continuation is cheaper.
