# T0b calibration A02 — Issue #7765

**Disposition: `PASS_CALIBRATION_ONLY`.** On 240 fully reconstructed training rows (20 separate seeds per condition and gain across gain-drift and cross-coupling), all six gain candidates reached every independent goal with zero bound violations and no audit errors. Gain 0.9 minimized aggregate corrections (131); next was 0.8 (138). This selects the fixed comparator parameter only. It is not a test of Jacobian adaptation. Held-out seeds 4000–4029 have not been run.

OrbStack image-store errors required the disclosed local CPython host fallback. This deterministic synthetic calibration makes no host timing/resource claim. A separate held-out freeze is required before the T0b candidate run.
