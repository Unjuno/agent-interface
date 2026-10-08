# LP evidence hierarchy container result

Task `LP-EVIDENCE-HIERARCHY-20260916-001`, Issue #536.

## Decision

**`PROMOTE_MEDIA_ONLY_EVIDENCE_SWAP_CANDIDATE`** as a development LP candidate. This is not a conversion result and does not yet mutate `site/index.html`.

## What changed in the candidate

No claim text, benchmark number, CTA, video source, link, ID or aria-label was added or removed. The candidate changes only evidence placement:

- the verified six-task desktop media figure occupies the hero-media position;
- the labelled failed Freedoom/MAP01 media figure occupies the later desktop-media position.

A second comparator moved the whole desktop section before the failed showcase.

## Container measurement

Chromium `144.0.7559.96`, Playwright `1.57.0`.

| Variant / viewport | CTA above fold | VERIFIED top | VERIFIED above fold | FAILED top | FAILED above fold | page height |
|---|---:|---:|---:|---:|---:|---:|
| baseline 1440x900 | yes | 2160.6 px | no | 572.1 px | yes | 3867 px |
| baseline 1024x768 | yes | 1961.9 | no | 540.5 | yes | 3546 |
| baseline 390x844 | yes | 2796.0 | no | 674.2 | yes | 4728 |
| whole-section reorder 1440x900 | yes | 662.1 | yes | 1372.8 | no | 3867 |
| whole-section reorder 1024x768 | yes | 630.5 | yes | 1249.4 | no | 3546 |
| whole-section reorder 390x844 | yes | 1161.4 | **no** | 1669.9 | no | 4728 |
| media-only swap 1440x900 | yes | **572.1** | **yes** | 2160.6 | no | 3840 |
| media-only swap 1024x768 | yes | **540.5** | **yes** | 1961.9 | no | 3527 |
| media-only swap 390x844 | yes | **674.2** | **yes** | 2796.0 | no | 4728 |

The whole-section reorder fails the frozen mobile first-viewport condition. The media-only swap passes all declared structural gates.

Page-height delta for media-only swap is -0.70% desktop, -0.54% laptop, and 0% mobile. CTA Y position is unchanged in every matched viewport.

## Structural integrity

Normalized baseline/candidate comparison reports exact equality for:

- visible text token multiset;
- href multiset;
- video source multiset;
- ID multiset;
- aria-label multiset.

All measured variants have zero duplicate IDs, zero scripts, and a valid `#main` skip-link target.

## Evidence boundary

The canonical landing-page Git blob at intake is `aa12064154b1d9d2972223bda31d2a9a740a6e22` / 26,191 bytes. Because the isolated container had no GitHub network access, the browser fixture was reconstructed from GitHub line reads and is 26,186 bytes, five bytes shorter. The DOM/content required by the measured checks is present and matched, but this prevents calling the run a byte-exact formal replay.

The experiment therefore supports a **layout implementation candidate**, not a production UX claim. The next implementation step should apply the media-only swap against the exact current blob and rerun the same three viewport gates with the real media files available before deployment.

## Limits

No human comprehension, conversion, Product Hunt, Lighthouse/network, playback-success, or page-load-performance endpoint was measured. In the isolated container, the real video files were unavailable, so screenshots show the desktop media element without its production media frame.

## ERROR CHECK

- three variants × three viewports = 9 layout measurements;
- CTA retained above fold 9/9;
- promoted candidate VERIFIED above fold 3/3;
- promoted candidate FAILED retained and later 3/3;
- duplicate IDs 0;
- scripts 0;
- skip target valid 9/9;
- text/link/video/id/aria normalized integrity all equal between baseline and promoted candidate.
