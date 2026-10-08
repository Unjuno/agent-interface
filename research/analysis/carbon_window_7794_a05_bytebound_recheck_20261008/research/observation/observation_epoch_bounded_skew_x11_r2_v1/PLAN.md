# Observation Epoch bounded-skew X11 R2

Parent #42; predecessor #1580.

## Fixed transfer

The R1 rule is unchanged. The newest acquisition is the anchor. Focus and target geometry are critical; they must be revalidated through that anchor. Image and UI context are noncritical and may precede the anchor by at most 2 ms. Session/surface/generation must match.

This controlled fixture maps one R1 tick to one millisecond. The 2 ms budget is frozen before construction and is never retuned.

## Acquisition

Private Xvfb with two Tk surfaces. X11 reads acquire focus, target geometry, a 16x16 ZPixmap ROI and window title. After noncritical acquisition, focus and geometry are read again. If a critical value changed, the adapter cannot certify its initial value through the anchor and fails closed.

Arms: STABLE, DELAYED_PAINT, STALE_FOCUS, IDENTITY_MISMATCH.

## H/T/D/C/U

H: real private-X11 acquisition exposes both the useful bounded-skew case and the stale-focus counterexample under the unchanged R1 rule.

T: construction8 rows/arm, then only if eligible formal64 rows/arm. Candidate, strict and naive comparators retained. Independent audit derives truth from raw initial/final focus/geometry and timestamps, not candidate validity fields.

D: candidate/oracle mismatch0; stale-focus candidate0; identity mismatch0; formal valid stable+paint >=96/128; naive stale-focus >0; strict admits fewer valid rows; exact 1024-byte ROI and focus restoration; integrity PASS.

C: Python/Tk/Xlib scheduling can exceed the budget; small ROI is not full-screen cost; final revalidation adds work.

U: private-X11 temporal composition only. No model/token/task-speed/general-GUI claim.
