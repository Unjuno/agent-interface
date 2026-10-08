# Maintained lineage tests in the existing CLI workflow

The primary CLI workflow omitted both maintained lineage regression modules.
A separate automatic workflow still ran the historical #2428 fixture, whose
two stale-receipt branches leave the sidecar evidence link stale and stop at
EVIDENCE_DIGEST_MISMATCH before the expected freshness refusal. #2456 already
added a correctly bound three-method fixture, and merged #6882 added five JSON
identity methods; neither was selected by the explicit primary CI command.

This repair appends those two existing modules to that command, and retires
the obsolete automatic workflow. PRIOR_WORKFLOW.yml.txt is its exact source;
PRIOR_FIXTURE.py.txt and both prior public failure logs retain historical
behavior. No runtime source, test expectation, original fixture, prior raw,
refusal precedence, digest validation or former experiment result is changed.
The existing three-OS matrix, Python3.12 setup, permissions, sparse checkout,
compile step, diagnostic doctor and push/pull-request path filters are retained.
No new job, workflow dispatch, status/check forgery or queue cancellation occurs.

On actual Windows/Python3.11.9, the updated workflow unittest command exited0:
129 methods, 123 passes and six explicit platform skips. The three freshness
plus five identity methods also exited0 under optimized Python. The unchanged
compile command exited0. Actual argv, UTC start/end, native exit, stdout/stderr
and source pins are in CHECKS.json and individual receipts/streams. A separate
existing doctor invocation exited0 and reports diagnostic selection only;
runtime availability there is not a tested native backend or input permission.

These are ordinary host verification, not hosted Linux/macOS/Python3.12
execution. The private cache prefix started empty for normal/optimized tests;
compileall explicitly wrote private .pyc files afterward despite the inherited
do-not-write environment. Those private files are not published. Neither the
old fixture nor any formal container/allocation, model, GPU, GUI or physical
input was invoked. The old failures remain failures, not relabelled PASS.

The tested source base is fb556b3d8bf5bae54a1f23b89fe2c2b5a2685df7.
CONTEXT.json qualifies result reuse against actual later main636986a8: selected
source/test/configuration and historical fixture bytes are unchanged. The
intervening #6900 compiled-run evidence-reference gate changes two run-body
lines; import-time definitions and the bridge-imported exception class are
unchanged, and that run body is outside this selected command. Newly added
core/guarded regressions are not implicitly selected. #6931 adds separate inert
evidence. This is scoped compatibility, not an all-core or future-main approval.

HISTORICAL_CUSTODY.json identifies exact prior Git blobs. Historical logs were
already public with <workspace> projections; this work copies them unchanged.
CONSTRUCTION_NOTES.md preserves later read-only inventory errors and the first
CRLF whitespace inspection failure. Archive-local .gitattributes preserves exact
Windows stream/receipt bytes with the usual whitespace checks and cr-at-eol;
no raw is normalized or test replayed. Both helpers are inert .py.txt custody images,
not automatic test/producer entrypoints. MANIFEST.json covers every artifact
except itself, while the workflow delta is verified separately from Git.

Parent #2428 remains a closed historical record. Claim5966175653 concerns this
narrow current routing defect, not a new execution allocation or ownership of
other CI jobs. Prospective distinct nonauthor content consensus, exact current
combined-tree review, actual required GitHub conditions, sole applier and one
expected-old forward application remain separate prerequisites for main.
No general computer-control, task-effect, physical release, recovery, latency,
model-efficiency or broad #57/#59 completion is claimed.
