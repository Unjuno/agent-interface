# Archived synthetic key-hold bounds result (2026-10-04)

**Disposition:** historical, one-shot 30-cycle fake-Xlib construction result;
not a live allocation, physical-input result, or current-main qualification.
The original README and all original output/source bytes are preserved under
`historical_originals/` or at their original package paths. The original
`SHA256SUMS.txt` and `PRE-RUN.json` were not rewritten.

## Result scope

The frozen run reported 30/30 fake-owner cycles without errors; its archived
raw-only auditor recorded 300/300 row checks and 11/11 aggregate checks. The
measurement was pinned to main `27f6e9ff02f21afbe56579b72063c19b2dbd74bb`
and #7440 head `99b7d130742b4e884709a862bc074d15e6b42ac9`. It bounds only the
synthetic XTest/server-side interval inferred from admission/up receipts. It
does not show when an application processes input or establish physical-key
state, game behavior, or useful task effect.

## Safe handling

This result is immutable. The original one-shot runner and writers for
`RAW-30.json`, `AUDIT.json`, `PRE-RUN.json`, `RUN.json`, and
`REPO-SOURCE-AUDIT.json` are archived as exact `.py.txt` files in
`historical_originals/`. The original README is there too. Their former entry
points now fail closed; they must not be used to recreate or retarget this run.

Use only the read-only verification command:

```sh
python -B verify_preserved_hold_bound_30.py
```

It checks the untouched historical checksum list and frozen source/output
links, mapping archived writer sources back to their original manifest names.
`test_preserved_evidence_safety.py` also checks the fail-closed entry points
and confirms the frozen artifact hashes do not change. Neither command reruns
the candidate or rewrites any retained evidence.

The old run is not a reproduction recipe. Any new measurement requires a
distinctly frozen successor, fresh source/runtime provenance, and a new
uniquely identified output path; this rescue does not authorize or execute
such a run.
