# Historical causal-order review rescue

Source `92cf265b15613b907b23504a53e4c487be0cad3e`, remote
`review/6928-causal-01a0ff52-20261003`. All 32 original files remain byte-exact.
The original independent review concerns PR6928 head
`5516baf54c92a120d651c08f4163707549678b04`, not its newer draft head
`fa8512b2f3d03601cea67986d45daf3fbcd5499e` observed during rescue.
No review vote or approval transfers to that newer head.

The retained comparison identifies seven causal/source-record corruptions
accepted by the historical V2 verifier, and five additional sanity controls
it rejected. All twelve were rejected by the historical independent oracle.
The original sixteen saved rows were not found false: 286 samples, 66 reads,
12 disposable file effects. This is finite authored-fixture evidence only.

The successor unittest checks original Git bytes and 31 manifest entries,
independently regenerates all twelve complete mutated RAW hashes from the
reviewed original RAW plus the saved replacement rows, and binds every
changed/unchanged artifact to its recorded hash. It checks saved result totals.
It does **not** rerun either verifier's semantic state machine, authenticate
private host custody, invoke a producer/native process, or qualify current
production behavior. The archived tools stay inert `.py.txt` sources.
The old verifier's coverage failure remains a failure, not a new PASS.

Run `python -B runtime/results/causal_review_rescue_92cf265/test_archive.py`
and repeat with `-O`. Repository Analysis Index CI is a separate gate.
Main integration and dependency checks are required before ref retirement.
