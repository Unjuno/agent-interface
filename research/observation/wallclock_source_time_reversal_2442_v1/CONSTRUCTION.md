# Excluded construction record

No formal rows existed during construction.

1. The first unittest command was launched from the parent directory, so `candidate` was not importable. This was a launcher working-directory error; no X11 construction/formal measurement ran.
2. After launching from the study directory, two unit examples failed because their synthetic `sample_ns` values used 100/200/300 nanoseconds while the intended examples were 100/200/300 ms. Candidate code and scientific gates were unchanged; only the excluded test fixtures were corrected to `100_000_000` etc.
3. Final preformal tests: 8/8 pass.
4. Separate live construction used only `REV110/P17/right` and `HOLD130/P11/left`, disjoint from formal reversal ages/phases. It completed two producer lifetimes and 12 captures. Independent construction audit passed 491,520 pixel-composition checks; maximum source-localization error was 0.965506471 px.

Construction output is retained in the evidence bundle but excluded from formal denominators. These corrections occurred before FREEZE.json and before any formal invocation.
