# Issue #8566 — typed/full artifact identity alias A01

## H / T / D / C / U

**H.** On exact current main, `reconcile_artifact` may report a typed event and its full observation as the same epoch when a duplicated JSON identity differs only by bool/int aliasing. The function currently uses Python equality for ID, step, sequence, capture time, and pointer binding. A valid exact pair should match; a single aliased identity must not.

**T.** Pin main commit `64c77d54c1a16b63be9084be1b117b628482b377`. Call the actual imported `reconcile_artifact` with a valid temporary PNG, two deterministic readers and otherwise-identical typed/full records. Run exact control, then single-field mutations for ID (`True` vs `1`), step (`False` vs `0`), sequence (`True` vs `1`), capture time (`False` vs `0`), and nested pointer-binding Boolean/integer value. Candidate and source remain unchanged during this baseline invocation.

**D.** The control must report `matched=true`. If any malformed alias also reports `matched=true`, classify `FAIL_BOOL_INT_ALIAS_ACCEPTED`; if every alias is rejected, classify `PASS_EXACT_IDENTITY`. Preserve the full raw rows, computed result, exact input source blobs, command, image/runtime identity, and process exit. An independent raw-only audit will reconstruct the comparison outcomes.

**C.** Deterministic local typed-artifact join only. No game, model, GUI, OS input, physical control, task effect, threat response, performance or MAP01 outcome is tested.

**U.** Direct function-boundary inputs may be malformed in ways normal upstream construction does not produce. This experiment establishes only whether this join itself enforces its exact identity claim. It does not establish exploitability in a full runtime.
