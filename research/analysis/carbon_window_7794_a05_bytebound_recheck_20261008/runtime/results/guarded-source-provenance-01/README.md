# Scoped-X11 source provenance integration

PR #5107 moved implementation into `runtime/guarded_x11_v1`. Its review found
that existing source manifests could hash only the compatibility wrappers,
leaving changes to the executed implementation unrecorded.

The new `guarded_source_dependencies_v1.complete_guarded_hashes` preserves the
existing relative-path conventions and records the seven shared implementation
files plus its own source. It refuses stale wrapper digests, conflicting shared
digests and missing implementation files. It does not update frozen outputs or
reinterpret a historical source pin. The package is included conservatively;
this is not a full third-party dependency closure or atomic execution pin.

32 producers are covered: 31 preregistration generators including inherited
source-list successors, and one offline retained-pixel probe. Historical
commit-pinned fetchers and fixed-allocation source/evidence remain unchanged.
`REPORT.json` in the archive enumerates the scope and exclusions.

Eight regression tests cover shared-byte changes with an unchanged wrapper,
root-relative and research-relative paths, conflicts/missing sources, unrelated
or vendored names, two actual generator main functions in fresh synthetic source
directories, all 32 producer call sites, and current shared relative imports.
Three existing runner source-gate loops reject a changed shared file before
execution. Their GUI/model phases are not invoked. Existing frozen experiment
paths are never used for these fixture tests.

Full local integration checks pass 231 protocol and 106 harness/distribution
tests. The first test-development failure (an AST list incorrectly called as a
function) is retained, as are the corrected checks and candidate source bytes.
No live experiment, model call, performance or token comparison is claimed.
Candidate sources were collected after the tests; no preregistration is claimed.

Run `python -O runtime/results/guarded-source-provenance-01/verify.py` to check
bundle inventory/hashes, source records, producer count and retained test-log
identity without extraction. This verifies byte consistency, not independent
authorship or a complete environment reconstruction.
