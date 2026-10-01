# #1522 fixed-ROI translation envelope A2

Decision: **RETAIN_FIXED_ROI_TRANSLATION_ENVELOPE_SCOPED**.

Direct predecessor #1495 is retained separately as `CHARACTERIZATION_EXECUTION_STOP_TIMEOUT_NO_RESULT`; it was not rerun. A2 changed only execution representation: the detector's exact 48x48 ROI distribution was generated directly and in batches instead of generating irrelevant 256x256 pixels outside the crop.

## Source-first construction

- sigma0 geometry oracle: 150/150 exact; mismatches0;
- scalar ROI vs batched ROI on identical supplied noise: 24/24 checks exact; mismatches0;
- inherited boundary construction reproduced: horizontal/vertical 4px non-invalidating and5px invalidating; diagonal2px non-invalidating and3px invalidating; relevant-change controls detected250/250;
- construction runtime:1.05s;
- first independent audit lacked construction-phase support and is retained failed; audit-only repair over the same raw passes. Construction was not rerun.

All source/evidence Git blobs were read back exactly before the fresh seed was used.

## Fixed-seed characterization

Fresh seed `149520260918002`, one invocation, reruns/replacements/tuning0. 75 cells =3 directions x25 integer translations; 1000 independent pairs/class/cell. Runtime **10.69s** on CPython3.13.5 / NumPy2.3.5 / Linux6.18.44 x86_64 with5 visible CPUs. CPU clock/host contention were not controlled.

| permitted translation | last d with FPR<=1% and FNR<=1% | first d with FPR>1% | first d with FPR>=99% |
|---|---:|---:|---:|
| horizontal | 4 px | 5 px | 5 px |
| vertical | 4 px | 5 px | 5 px |
| diagonal `(d,d)` | 2 px | 3 px | 3 px |

The observed boundary is sharp in this fixture:
- horizontal d=4: FPR0/1000, changed-count96 median; d=5: FPR1000/1000, median120;
- vertical d=4: FPR0/1000, median96; d=5: FPR1000/1000, median120;
- diagonal d=2: FPR0/1000, median88; d=3: FPR1000/1000, median126.

Relevant +16 semantic-change FNR is **0** at d=0 and maximum FNR across all75 tested translation cells is **0**.

Primary audit: PASS/errors[], corruption controls6/6. Independent geometry/bound audit: PASS/errors[]. Result SHA-256 `8b748b4ca1beb4499e442453aabea5fa7283f1d6302a1902c7e78f2505f9ffb8`.

## Interpretation

The predecessor's scoped ROI change detector is not translation-invariant. In a policy where target translation is *allowed*, the same fixed 100-pixel invalidation threshold begins revoking solely because of geometry at5px one-axis translation or3px diagonal translation in this synthetic fixture. The relevant-change signal remains strong, so the identified failure is false invalidation from permitted motion rather than loss of sensitivity.

This supports the predecessor report's recommendation to test a bounded current revalidation/search mechanism before simply enlarging the ROI. It does **not** select or validate that repair. The safe architecture remains: this detector may be a bounded no-authority invalidation sentinel only inside a declared spatial applicability envelope; outside it, revalidate/fallback rather than interpreting the raw changed-pixel count semantically.

## Limits

Independent Gaussian sigma2 noise, fixed contrast/geometry, synthetic image arrays, no X11/capture/compositor, no target identity, no task efficacy/model/token/human-tempo/production claim.
