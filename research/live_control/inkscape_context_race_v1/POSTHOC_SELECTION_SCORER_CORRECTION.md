# Posthoc correction to Issue #321 visual-selection evidence

The original #321 `selection_blue_pixels=276` criterion was not selection-specific; it included stable Inkscape ruler/chrome pixels. Recomputing the 20 retained `revalidated.png` frames with the actual black selection handles on A (top/right/bottom; thresholds top>=30, right>=80, bottom>=30) yields visible A handles in **16/20**, not 20/20.

Missing-handle cases: `case-07-stable`, `case-10-switch`, `case-14-switch`, `case-17-switch`.

The persisted SVG effect result is unchanged: stable A+10/B0 10/10; switch A0/B+10 10/10. In particular, stable case 07 moved A despite no painted handles at the revalidation frame, directly demonstrating that painted selection state can lag semantic selection.

This correction retracts only the narrow claim that the saved screenshot independently proved A selected in 20/20. It does not edit or replace any first outcome. Exact recomputation was performed from the retained full archive SHA-256 `7184ed8a643a1ceb8d32cbbb0c9ba56cfa38f19db885549326dcaf7491dc2649`; the detailed recomputation JSON is retained with successor Issue #327 evidence and the result comment on #321.
