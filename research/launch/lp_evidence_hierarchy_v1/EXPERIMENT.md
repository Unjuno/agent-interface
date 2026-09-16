# LP evidence hierarchy container experiment

Task: `LP-EVIDENCE-HIERARCHY-20260916-001`

Publication branch: `research/lp-evidence-hierarchy-20260916-001`

Baseline landing-page blob: `site/index.html` Git blob `aa12064154b1d9d2972223bda31d2a9a740a6e22` (26,191 bytes).

## H

The current landing page places the labelled failed Freedoom/MAP01 recording immediately below the hero while the verified six-task desktop evidence appears much later. Holding copy, claims, CTA, styling and both recordings fixed, moving only the verified desktop media into the hero-media slot and moving the failed Freedoom media into the later desktop-media slot should make the first viewport evidence-first without hiding the failed result.

## T

Container-only development comparison using Chromium 144 / Playwright 1.57. Three variants were rendered from the current static LP structure:

1. `baseline`: current ordering;
2. `candidate_reorder`: move the whole desktop evidence section before the failed showcase;
3. `candidate_swapmedia`: swap only the two media figures, preserving surrounding section copy/order.

Viewports: 1440x900, 1024x768 and 390x844. Measurements: document Y position and above-fold state of `View source`, `VERIFIED RUN`, and `FAILED RUN`; page height; duplicate IDs; script count; skip-link target. No network/user analytics and no claim about conversion rate.

The local baseline reconstruction used GitHub line reads and preserved the page DOM/content needed for this experiment but was 26,186 bytes, 5 bytes shorter than the canonical blob; therefore this is a development/layout result, not a byte-exact formal browser replay.

## D

Promote only the structural candidate that satisfies all three viewports:

- hero CTA remains above fold;
- `VERIFIED RUN` appears above fold;
- `FAILED RUN` is ordered after `VERIFIED RUN` and remains in the page;
- duplicate IDs = 0;
- script count stays 0;
- skip link remains valid;
- page height changes by less than 2% from baseline.

## C

First-viewport evidence ordering may improve perceived credibility but this experiment does not measure human comprehension or conversion. Swapping media may also reduce the visual drama of the hero because the retained desktop video has no explicit poster in the current markup.

## U

Static Chromium layout only, three viewports, local media bytes unavailable in the container. No Lighthouse/network-load measurement, user study, Product Hunt conversion claim, or production rollout claim.
