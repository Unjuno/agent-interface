# App-server explicit UTF-8 rescue

Original source `77d8f0a2dc43fef22ac73fa804350389edd898e1`, old delivery #6991. Rescue base `b88986df5be3fdc4784ad990b2bfa30beda1c8fd`.

Extracted only Popen `encoding="utf-8"` onto current client, keeping current Boolean-ID, EOF, journal and reader-retirement changes. Original three-method regression is restored exactly, and appended once to the current native protocol roster without removing newer modules. Existing fake process factories must accept the standard Popen keyword. This deliberately sets the text pipes to UTF-8, with no replacement/fallback encoding.

Original 26-file packet `research/live_control/appserver_utf8_repair_59_20261003_01a0ff34` is Git-byte-identical; all25 published manifest entries match length/SHA256. Original publication STOPs, first results and reused native capsule remain untouched. No historical native peer or producer/auditor replay occurred.

Fresh Python3.12 RED on current base: three tests, one literal accented mojibake failure and one Japanese closed-reader error, exit1 (`red.log`). With explicit codec, new3 plus current EOF/reply-ID/journal/retirement suites pass19/19 normal and -O (`green.log`, `optimized.log`). These are controlled actual TextIO byte-decoding tests, not a live provider/server certificate.

Full macOS native integration is **FAIL**, not PASS. Exact baseline production/runner was checked against the base before running: protocol440 tests,4failures6errors5skips; harness205 tests31errors. Candidate protocol443 tests, same4failures6errors5skips; harness205 same31errors. All41 ERROR/FAIL entries are identical in both fresh runs (`native-comparison.log` lists every name; full byte-exact `native-baseline.log` and `native-candidate.log` retained). Missing Linux `/proc/self/ns/pid` affects native-owner tests; portable-stdio and downstream assertions also fail. No failure is suppressed or fixed in this rescue, and unchanged roster is not proof of whole-repository correctness. Linux hosted gates remain necessary.

H: explicit UTF-8 preserves literal replies/notifications under locale-default decoding.
T: current-source RED/GREEN, normal/-O19 methods, baseline/candidate full native suites, exact packet/manifest and local CI.
D: scoped19/19; packet26 exact /manifest25 matches; fullmacOSnativeFAIL with identical41-error/failure roster.
C: controlled decoder factory is not real provider, and no generic custom-factory or invalid UTF-8 behavior is established.
U: original native peers/formal allocations unrerun; fullnative/macOS, live task/backend/model/timing remain unproven.

Local CI completed exit0 with `LOCAL_CI_SUMMARY: steps=43 failures=[]`, recorded separately in `local-ci.log`; this does not override the full native FAIL above. OrbStack image inspection has daemon-blob operation-not-supported STOP; no container, reset/prune/pull or unrelated/shared allocation used.
