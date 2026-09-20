# Construction and preregistered-gate record

- Base image: `mixed-app-identity-2782-local@sha256:e6ced3789130dae21c7b42b7b9d25cd590a271a77910e16c01d2edf87e44cee6`.
- Derived image: pinned in `FREEZE.json`; Linux/arm64. Build-only network was required for Debian packages. Formal/preflight containers use `--network none`, read-only root/source, and tmpfs/evidence mounts only.
- Construction preflight on the derived image returned `PASS_XAUTH_COOKIE_IDENTITY_FILTERED`: one selected window per app; distinct IDs Inkscape `2097159`, Calc `6292261`, Chromium `4194307`; auxiliary candidates remained non-selected; input/model/network calls 0.
- First preflight construction attempt stopped before launching apps because the derived image lacked `xauth`. This was a construction-only STOP, not a formal attempt. `xauth` was added to the image recipe; the image was rebuilt and assigned a new digest before freezing.
- Pinned-container unit tests: 7/7 pass, including missing and ambiguous identity refusal before geometry, `geom(None)` guard, exact role filters, and process cleanup on failed readiness.
- Formal-launcher gate is fail-closed and checks source/prereg/freeze/launcher hashes, image ID/platform, unit tests, distinct-window construction preflight, and fresh output before the single formal invocation.
