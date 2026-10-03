# V3: requested cancellation completes before gate release

The original actual asyncio allocation and v2 repair remain unchanged. Independent
nonauthor reviews5398805286/5398828832 found16 effective fixed-fixture gate-order
contradictions that both v1 and v2 accept. Their successful earlier controls did
not establish complete causal coverage. The v3-redistribution content proposal is
HOLD; superseded approvals remain historical and do not count for application.

Root cause: frozen candidate.py awaits gather of explicitly cancelled waiters
before gate_open. Target waiter terminal and finally-detach precede that gather
completion. V2 required request<gate and request<target terminal<detach, but did
not join target detach<gate. New standalone audit_v3.py retains all v2 checks and
adds that target-specific edge for cancel_first/cancel_last. It imports no old
auditor/candidate/runtime. It requires only the named requested waiter; direct
propagation can cancel other waiters whose finalizers were not awaited here.

Actual ordinary retained-data verification: nine regression methods pass normally
and optimized after the preserved v2-delegating RED has16 assertion failures,
exit1, across the16 partial-cancel rows. The exact independent row6 witness is
SHA256f6e789430da805a5a29e9b7ba601e115a0cbaaa53c0dc78afd3c0e39fcfb7f19.
All16 stored full copied traces remain v1/v2 false accepts and reject under v3 for
the requested-waiter detach-before-gate reason. All25 previous controls still
reject. The ordinary new audit CLI exits0 on unchanged raw, returning48rows /
120outcomes /0errors, `PASS_RETAINED_TRACE_V3_SCOPED`.

Original raw136089 bytes SHA256d3262358814f4fd724d0b36b0fc027d2b4fee70f5a7e56a090d8ee794c5c2441.
All44 package files from c9d8c0cf (original plus v2) remain byte-identical; neither
old manifest is rewritten. This supplement has its own manifest and source/input
FREEZE. Source-freeze commitab01a9a61919b710b3fad367db88d51e3ede7653 precedes the
new retained-control/audit CLI; it binds18 source/plan/RED/GREEN files and six old
immutable input hashes. FREEZE is ordinary post-discovery, not experimental
preregistration. The new source-freeze tests preceded this freeze as documented.
Actual command/UTC/exit/stream identities are in execution receipts. Public
stack traces redact only the owned repo path prefix; exact originals remain
private with their hashes.

The first whitespace check flagged unittest's trailing space in the preserved RED
stderr. Publication-only log attributes now exempt those exact log bytes from
whitespace normalization; none of the18 frozen files was rewritten. `.gitattributes`
is later publication metadata bound by the final manifest/head, not a substituted
execution-source freeze. Authored source/docs are AST/whitespace checked. New v3
scripts are excluded from pytest discovery and are invoked explicitly; broad
historical candidate discovery/replay was not performed. Supplemental footprint
stays below4MiB;16 exact copied witness files total2177424 bytes. Original source,
image, guest/output, formal allocation and scientific first outcome were not run
again. Formal replay count0; these checks are ordinary retained-data work.

Limits: this closes one known await-order omission and does not prove arbitrary
event-emission authenticity or exhaustive verifier correctness. The observed
shielding/ownership contrast remains descriptive scoped evidence. No dynamic
joins, TaskGroups, blocking-I/O termination, GUI/task-effect/currentness/authority,
natural demand, timing/efficiency, portable backend or production adoption claim.
New head/digest and explicit renewed votes by the same fixed committee are needed.
Current-main combination, actual rules and one expected-old forward application
remain separate. No author main send or apply/resource lock is held.

Read-only commands: `python -B -m unittest discover -s repair_v3 -p test_audit_v3.py -v`
from the study root, or audit_v3.py on the original execution/raw.json with its
exact expected raw SHA and a fresh output path. Do not rerun the consumed candidate
or formal allocation. Copied controls are retained; rerunning characterize.py in
this published folder intentionally refuses the already-existing output directory.
