# Formal-01 result

- Issue/allocation: #3645, `issue2499-readiness-successor-3634-formal-01`.
- Decision: `STOP_MIXED_APP_READINESS_SUCCESSOR` at first Inkscape readiness; no app was admitted and no transition/input ran.
- One formal invocation, zero retries; input/model/network calls 0.
- Xauthority setup was present in the event ledger (`cookie_auth_file`, cookie added true); Xvfb socket and all process groups cleaned up.
- Independent audit: `PASS_AUDITED_EARLY_STOP`, 0 errors, 3 events; task effect not tested.
- Inkscape package version in pinned image: `1.2.2 (b0a8486541, 2022-12-01)`.
- Frozen source commit: `c8a25969563876c9f5d0348eb4fb71c132eea0f8`; image `sha256:f8ae93cfedd412cfe39ca575a97abc32c4d6e99ee7b5cc7848e79e0ce08bdc9f` (`linux/arm64`).
- Raw result SHA-256: `099c7875e9b72357590be97c1fe1ef2c1b8fdd8a336c3a017fa9687b1280f971`.
- Preflight SHA-256: `d67c27e3c3c850d6bebe79f524b5f24b5f746d3e8e74ad5ab4a0455fb8e6a658`.
- Audit SHA-256: `0be218a538d9493c4a939aade55dc46c885d7d2f74eca367a6c702b9f562d055`.

The root cause was isolated in a separate, non-formal container diagnostic and is documented in `DIAGNOSTIC.md`. The formal result remains immutable; do not rerun this allocation.
