# V3 marker repair and historical identity mapping

The original pointer-location source and evidence were published at
`c97aa0b0a086a64f029a16feef98738157f216d1`. The original `MANIFEST.json`,
README, source snapshots, fixtures, raw, audits and failure logs are preserved
unchanged. Their source identity is that historical head, not a claim that
every original source path still has the same bytes in the v3 tree.

In particular, the original manifest entry for
`runtime/cli_v1/receipt_references.py` binds SHA-256
`ca8bab6667b55827db29191228125406bd5e9a2fc3dcf7233a083c629657bae3`.
Those exact bytes remain both in the original Git head and in inert
`event_boundary_v2/source.py.txt` and `event_marker_v3/baseline.py.txt`.
The original pointer regression module is unchanged. The earlier native and
event producer results are not rerun, relabelled or pooled as v3 observations.

V3 changes one additional public-event marker equality to use the existing
canonical JSON encoding. A declared integer reference map must have the same
integer marker; Python Boolean/float aliases are not identical JSON markers.
In the old alias cases the map still chose its declared event index. This is
marker consistency, not evidence of wrong-event selection, input authority,
native effect or performance. Pointer resolution and native decoding are
unchanged; seven new marker regressions accompany the original ten pointer
regressions. The generic malformed-container/Python-object boundary remains
outside this change.

The new prospective source/fixture/auditor freeze and separate raw result are
under `event_marker_v3/`. That directory's manifest binds the v3 source/test
and new artifacts. It explicitly maps the historical original-manifest source
entry to its retained witness, rather than changing the old manifest to match
a new source. Actual current-head checks and content approvals are separate
records outside the source tree. Earlier proposal epochs are superseded for
application; a fresh proposal and two distinct nonauthor votes are required.
