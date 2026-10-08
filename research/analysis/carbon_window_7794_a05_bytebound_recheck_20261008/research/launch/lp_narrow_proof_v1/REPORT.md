# LP narrow-height verified-receipt experiment

Task `LP-NARROW-PROOF-20260916-001`, Issue #576.

## Decision

**`PROMOTE_HERO_VERIFIED_RECEIPT_COPY_SCOPED`** as a copy candidate.

The full VERIFIED media already enters the first viewport at 390×844 and 360×740, but at 320×568 its label begins at y=712.078 px. Rather than hiding hero content or shrinking the media, this experiment changes only the existing hero-description sentence to lead with the retained desktop receipt:

> Verified desktop evidence: 6/6 exact submissions · 3 model generations. Reusable GUI skills and guarded local loops; escalate when judgment is needed.

The numerical receipt is already supported by the retained desktop run; this experiment does not introduce a new capability claim.

## Container result

Chromium 144 / Playwright 1.57, five matched viewports.

| viewport | proof phrase top | proof above fold | description height | CTA Y | VERIFIED-media Y | page height |
|---|---:|---:|---:|---:|---:|---:|
| 1440×900 | 304.844 px | yes | unchanged | unchanged | unchanged | unchanged |
| 768×1024 | 489.969 | yes | unchanged | unchanged | unchanged | unchanged |
| 390×844 | 398.078 | yes | unchanged | unchanged | unchanged | unchanged |
| 360×740 | 413.297 | yes | unchanged | unchanged | unchanged | unchanged |
| 320×568 | 409.688 | **yes** | unchanged | unchanged | unchanged | unchanged |

Horizontal overflow remains zero; scripts and duplicate IDs remain zero.

## Boundary

At 320×568 the full video is still below the first fold. The candidate only ensures that a truthful verified-evidence receipt is visible inside the existing hero copy footprint. It does not move or duplicate the video.

The original and candidate description occupy the same measured height in all five viewports, so this candidate does not obtain its result by hiding content, reducing font size, or pushing the CTA/media down.

## Limits

Static browser geometry and copy provenance only. No user comprehension, credibility, click-through, conversion, accessibility-user or page-load endpoint was measured.

## ERROR CHECK

- exact baseline blob: `34d778d6113fbbf98843b4e0506afddcbc3dfdb6`;
- five baseline/candidate viewport pairs measured;
- proof phrase above fold: 5/5;
- description height unchanged: 5/5;
- CTA Y unchanged: 5/5;
- full VERIFIED media Y unchanged: 5/5;
- page height unchanged: 5/5;
- horizontal overflow: 0/5.
