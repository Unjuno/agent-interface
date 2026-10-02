# Explicit retained Python dispatch summaries

Base a7817597b8405f9b7581820fe79c9242a5f65255. Add
`summarize_retained_dispatch(view, report_path, run_directory)` to the public
summary module and make the existing CLI helper delegate using its unchanged
`report.json` convention. Python callers can retain their own filename without
inventing an MCP call ID or copying a report to a reserved name.

The helper reads only the explicitly supplied report, checks exact length/hash
against the full received-byte presentation, and reuses the existing success-only
summary gate unchanged. No file writing, input, image capture, replay, source
refresh or default presentation change is introduced. Full fallback remains for
changed/missing/unsupported reports, failed input, uncertain release and recovery.
The original PNG, reference, outcome, capture/release records are preserved.
Partial omission and hash-pinned full retrieval remain explicit. The current guide
shows `review_bytes` plus this helper; file `review()` can return v1 when compaction
is not smaller and therefore deliberately remains full under this gate.

## Paired retained evidence

The two successful draw/save reports from the preceding primary Inkscape run
were used read-only. Their immutable report bytes and selected PNGs were unchanged;
this is not a new GUI allocation, live perception comparison or model experiment.
`pair_projection.py`, full/summary/retrieved JSON, `pairs.json` and logs retain both
representations of the exact same evidence. Text sizes use canonical UTF-8 JSON
with the image payload removed from both representations:

| Report | Full text bytes | Summary text bytes | Reduction |
|---|---:|---:|---:|
| Two-drag batch |4,910|3,578|27.1%|
| Save batch |3,999|3,558|11.0%|

Original images, image references and outcome summaries compare equal. Library
retrieval returns the full original report exactly; a real CLI `review` invocation
using the returned report path, digest, image directory and `--no-image` also
returns the same full report without image delivery or input. The received-byte
source hash here names the exact retained file encoding, which differs from the
previous live in-memory serialization; both dictionaries represent the same report.
No digest is silently treated as the other encoding's identity.

Synthetic retained variants with recovery required, a failed release and an
unknown execution field all keep full evidence. They do not simulate actual new
GUI faults. Initial exploration encountered absent sparse-checkout historical
files, then the expected v1 full fallback from file `review()`. Materializing the
exact existing files and using the documented received-byte representation resolved
the read-only study, without changing the success gate or replaying input.

## Validation and limits

The red test records the missing new helper before implementation. An initial
test fixture lacked an image member and its failure is retained in `normal.stderr`;
the corrected preservation test explicitly supplies one. Final71 related tests
pass normally and under `-O`, including the unchanged CLI route. Complete native
WSL checks pass397 protocol/192 harness tests, with complete hashed logs retained.
The prior application task/primary use remains scoped to its pinned source.

This is production reuse of an existing opt-in projection and removal of a local
filename restriction. Offline bytes are not actual model tokens, billing, useful
feedback, semantic completion, speed or human tempo. `pairs.json` leaves model
usage and billing unavailable; no token reduction is inferred. A fair fresh model
comparison remains required before choosing a summary default or claiming latency
or cost benefit. Frozen Inkscape/Calc studies and production defaults are unchanged.
