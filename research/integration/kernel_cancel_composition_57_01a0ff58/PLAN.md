# Three kernel repairs: finite composition construction for #57

Question: can release-evidence refusal, cancellation freshness and missing-receipt
occurrence reporting compose without granting authority or losing uncertainty?
H: three existing repairs jointly reject stale release evidence while preserving
possible occurrence after accepted begin when no accepted execution receipt remains.
T: eight subsets of R/C/U, twelve fixed sequential histories each, one native
CPython child per subset, 96 rows total. No prior author matrix is rerun.
D: PASS_COMPOSITION_SCOPED only if the separate raw-only oracle reconstructs all
96 typed event/outcome rows and the complete inventory, and all three together
preserve positive equality/later controls while refusing the two stale boundaries.
Otherwise retain FAIL/HOLD with first outputs. No author/runtime patch repair here.
C: identical four base kernel modules and identifiers, timestamps and calls;
only exact source subsets differ. Oracle imports no tested module or producer.
U: sequential typed synthetic one-clock API records; not physical release, clock
provenance, backend authenticity, concurrency, application effects or performance.
Missing-receipt possible occurrence is conservative uncertainty, not observed effect.

Base: main a394fcdd4254679df4265622b8ae6d0f8e251849.
R: PR6861 f3ecf397ae8618cf700e8f6b927bb688e32a42b4 (contracts.py).
C: PR6892 d06e636a8c35715d371dc6ba00632aab4b3bad3c (lifecycle.py).
U: PR6894 fa276a1c5b85c45251f2ffd175e65fb18836d664 (lifecycle.py).
Base production bytes must equal both source parents on the changed files.
For C+U, Git merge-file performs an exact three-way source-only composition,
requiring exit zero; no manual conflict repair or private feature toggles.
This is a four-module source composition, not a full repository merge certificate.

Fixed times: observation100, authorization200, accepted begin300, receipt
start400/end500, expiry1000. Cases: pre-start release399 with NONE/OBSERVED,
equal-start release400 NONE, after-end release600 POSSIBLE; cancel299/300/600;
no begin; expired begin1000 refused; duplicate begin200/800 refused with cancel
250/400; stale cancel299 followed by fresh600 only when the first was refused.
Receipt construction, record admission, stop and outcome are separately visible.

All source, fixtures, producer and oracle are prospectively frozen. First raw and
child UTC/command/exits/stdout/stderr are immutable. Afterwards, copied-data
corruption controls and all-three source regressions may run separately as ordinary
verification. No formal allocation, backend/input/GUI/model/container/GPU or shared
lease. No extra worker spawned. The independent implementation is by this author;
non-author consensus is separately required for any evidence/main delivery.
