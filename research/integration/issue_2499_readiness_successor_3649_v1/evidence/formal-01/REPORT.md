# Formal-01 result

- Issue/allocation: #3649, `issue2499-readiness-successor-3649-formal-01`.
- Decision: `STOP_MIXED_APP_READINESS_SUCCESSOR` at Calc readiness after Inkscape resolved READY; Calc process started but no Calc role window was admitted. No transitions or input ran.
- One formal invocation, zero retries; input/model/network calls 0; all process groups and Xvfb socket cleaned up.
- Independent audit: `PASS_AUDITED_EARLY_STOP`, 0 errors, 3 events; task effect not tested.
- Frozen source `f00417eb3da32de7f53e56b00f2d117f8d2d7656`; pinned image `sha256:f8ae93cfedd412cfe39ca575a97abc32c4d6e99ee7b5cc7848e79e0ce08bdc9f`, linux/arm64.
- Raw result SHA-256: `4ef4ef18c6e7892b994160a846913fc147b58cc5953ce93fe38c156f98303b95`.
- Preflight SHA-256: `d67c27e3c3c850d6bebe79f524b5f24b5f746d3e8e74ad5ab4a0455fb8e6a658`.
- Audit SHA-256: `da464db582cc4e7ed1f7843581a883d83cfcdecc56b10bae08396afca4a15b29`.
- Successor hypothesis: the formal launcher adds `--nodefault` to LibreOffice while the passing construction reference does not. This difference is recorded for fresh verification, not claimed causal.
