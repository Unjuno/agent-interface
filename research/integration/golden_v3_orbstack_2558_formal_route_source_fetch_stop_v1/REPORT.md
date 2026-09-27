# #2558 formal route source-fetch stop

Date: 2026-09-20 Asia/Tokyo

## H/T/D/C/U

- H: the official preregistered Chromium integrated route can only be treated as an experiment when the complete frozen repository tree is available in the container; a hand-copied subset is invalid.
- T: retrieve the complete main tree, materialize it in the local experimental environment, then run the official `research/live_control/run_integrated_efficiency_live_v1.py` entrypoint in the pinned Docker route.
- D: STOP before allocation. A shallow HTTPS git clone remained without a resolved HEAD/checkout after more than two minutes and its shallow lock remained active. A codeload tarball request timed out after 30 seconds with 34MB received; the endpoint did not support byte-range resume. No official Chromium allocation, model call, task action, or route metric was counted.
- C: `STOP_FORMAL_ROUTE_SOURCE_FETCH_TIMEOUT`.
- U: obtain the complete main tree through a working repository transport, verify commit/source hashes against the preregistration, build/run the official container route, and retain the first complete or failed allocation without retrying it.

This stop is separate from the successful additive Docker fixture experiments already merged for #2558. No prior result was changed.
