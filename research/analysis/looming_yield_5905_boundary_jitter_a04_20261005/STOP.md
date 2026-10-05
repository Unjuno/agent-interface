# A04 — FAIL_INTEGRITY_AUDITOR_INPUT_SCHEMA

The frozen A04 candidate ran once and exited 0, emitting 36 candidate rows
(31 eligible). The separate frozen auditor ran once and exited 1 before writing
an audit JSON. Preserved stderr:

`TypeError: string indices must be integers, not 'str'` at
`metric_frontier`: the A04 generator serialized auditor truth as an object
containing `schema` and `cases`, while the retained A09 auditor requires the
truth JSON root itself to be a list of case records. This is an input-schema
integrity failure, not a scientific TTC result.

Exact command, invocation counts, candidate-output hash, and exits are in
[RUN_RECORD.json](RUN_RECORD.json); complete stderr is
`results/auditor.stderr.txt`. Candidate=1, auditor=1, retries=0. No rerun,
manual audit substitution, or post-hoc scientific claim is made. A05 changes
only the truth-sidecar envelope, uses a fresh seed, and is a distinct successor.
