# LP inline hit-area container experiment

Task `LP-HIT-AREA-20260916-001`, Issue #571.

## Decision

**`PROMOTE_44PX_INLINE_HIT_AREAS_SCOPED`**.

A five-viewport Chromium geometry audit found no horizontal overflow, broken ARIA reference, or duplicate-ID problem in the current LP. The only elements below a project-defined 44 px interaction-height gate were the two evidence-report links and footer license link.

The one-factor candidate changes only those CSS rules to `display:inline-flex; align-items:center; min-height:44px`.

## Measured comparison

| viewport | baseline <44 px | candidate <44 px | page-height delta | overflow |
|---|---:|---:|---:|---:|
| 1440×900 | 3 | 0 | +0.78% | 0 |
| 768×1024 | 3 | 0 | +0.60% | 0 |
| 390×844 | 3 | 0 | +1.17% | 0 |
| 360×740 | 3 | 0 | +1.14% | 0 |
| 320×568 | 3 | 0 | +1.08% | 0 |

Baseline evidence-report links measured ~29.19 px high; footer `Apache-2.0` measured 35 px. Candidate versions are exactly 44 px high in all five viewports.

Hero CTA and VERIFIED media Y positions are unchanged in every matched viewport. Duplicate IDs and invalid `aria-labelledby` references remain zero.

## Separate observation

At 320×568, the verified media begins at y=712.078 px and therefore does not enter the first fold. That is true in both baseline and candidate. It is a separate narrow-height information-hierarchy question; do not attribute it to the hit-area change.

## Interpretation

This is a project ergonomics/layout gate, not a claim that the baseline violated WCAG AA. The result only establishes that the three smallest inline targets can be normalized to a 44 px vertical interaction area with low structural cost in the measured static LP.

## Limits

No real touchscreen error rate, keyboard task time, screen-reader study, human comprehension, conversion or page-load performance was measured.

## ERROR CHECK

- exact baseline Git blob `34d778d6113fbbf98843b4e0506afddcbc3dfdb6` matched the local measurement bytes;
- 5 matched viewports × 2 variants measured;
- candidate small-target count 0/5 viewports;
- horizontal overflow 0/5;
- page-height increase <2% 5/5;
- CTA/VERIFIED Y unchanged 5/5.
