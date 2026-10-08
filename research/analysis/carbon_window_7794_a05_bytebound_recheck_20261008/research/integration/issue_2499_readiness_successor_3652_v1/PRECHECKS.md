# Construction and preregistered-gate record

- Base image: `mixed-app-identity-2782-local@sha256:e6ced3789130dae21c7b42b7b9d25cd590a271a77910e16c01d2edf87e44cee6`.
- Derived image: pinned in `FREEZE.json`; Linux/arm64. Build-only network was required for Debian packages. Formal/preflight containers use `--network none`, read-only root/source, and tmpfs/evidence mounts only.
- Predecessors #3633, #3645, and #3649 formal-01 STOPs remain immutable. #3649 passed Inkscape readiness but stopped at Calc; separate construction diagnosis found a Calc role window without `--nodefault` and no role window with it.
- First preflight construction attempt stopped before launching apps because the derived image lacked `xauth`. This was a construction-only STOP, not a formal attempt. `xauth` was added to the image recipe; the image was rebuilt and assigned a new digest before freezing.
- The cookie-authenticated construction preflight returned `PASS_READINESS_CONSTRUCTION`: Inkscape `2097159`, Calc `6292261`, Chromium `4194307`, all distinct; source gate `PASS_XAUTH_COOKIE_IDENTITY_FILTERED`; input/model/network calls 0. It uses the exact Xauthority-cookie and `Xvfb -auth` mechanism adopted by the formal runner.
- Pinned-container unit tests: 9/9 pass, including missing and ambiguous identity refusal before geometry, `geom(None)` guard, xauth-cookie setup and refusal, exact role filters, and process cleanup on failed readiness.
- Formal-launcher gate checks source/prereg/freeze/launcher hashes, image ID/platform, unit tests, distinct-window construction preflight, and fresh output before the single formal invocation. A typed early STOP is audited and retained rather than suppressing the independent audit receipt.
