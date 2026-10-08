# Explicit vs autonomous key-up receipt semantics — #5156 construction v2

## H / T / D / C / U

### H — falsifiable hypothesis

Separating `explicit_client_up` receipts from `autonomous_cleanup` receipts
allows a valid owner-thread XSync interval to remain auditable without
inventing a synchronous caller bracket for expiry, cancellation, focus loss, or
owner shutdown. Explicit releases must be nested in their exact caller RPC;
autonomous releases must instead carry a typed cause and no caller timestamps.

### T — bounded construction experiment

- Intake main: `c2f0eb2dc03d6949942be7f8ccb463f41975393e`.
- Pinned source context: `input_owner_v10.py` blob
  `341b3c01649943ddaad5f28431a792c4889cc36e` and
  `input_transition_owner_v3.py` blob
  `0ea631abcf6272f0538a9ef9198ad8069b47b464`.
- Allocation: `MAP01-OWNER-KEYUP-RELEASE-SEMANTICS-5156-20260928-02`.
- Run a frozen stdlib-only synthetic receipt contract suite and a separate
  reference-oracle audit on host CPython 3.12.10. No owner thread, X11/XTest,
  GUI, user input, model/provider, GPU, network, or Docker is invoked.
- This is an explicit-only protocol construction rung following PR #5160's
  source finding that autonomous owner releases can occur outside caller RPCs.
  It does not consume or retry #5156 allocation 01's unstarted X11 fixture.

### D — decision gate

`PASS_RELEASE_EVENT_CLASSIFICATION_CONSTRUCTION_SCOPED` requires all frozen
directed tests to pass; the independent oracle to agree on every valid and
corrupted vector; explicit owner brackets to satisfy
`caller_start <= owner_release_start <= owner_sync_return <= caller_return`;
autonomous cleanup to have an allowed reason and no caller bracket; stale or
unowned keys to produce no accepted physical-release receipt; and all authority
flags to remain false. Any false acceptance, source mismatch, or auditor
disagreement is FAIL/STOP and retained. A PASS authorizes only a subsequent
isolated X11 construction, not MAP01 integration or scientific claims.

### C — controls

Controls cover single-key explicit up, ordered two-key up, partial admission
cancel, autonomous expiry, stale explicit up, owner error, inverted clocks,
caller-boundary violation, unknown automatic cause, duplicate request/sequence,
and attempted authority promotion. The reference auditor uses a separately
implemented oracle and seeded generated vectors. Historical v38/v39 and #443
outputs are untouched.

### U — uncertainty and limits

No X server or InputOwner implementation executes here. The construction does
not prove that the proposed receipt can be emitted by the real thread, that
XSync completion is physical/application consumption, that interval censoring
narrows under load, or that MAP01 control improves. Shared disposable X11/
container execution remains separately gated by explicit queue assignment.

## One-shot frozen command

`FREEZE.json` pins candidate source hashes, source-context blobs, interpreter,
command, and a new empty output directory. The sole post-freeze command is
`python -B run_once.py <package-root> <package-root>/results/host-01`.
The runner stops if the output exists or any frozen source hash differs.

## Pre-freeze construction history

Before the allocation was frozen, the 12 directed `unittest` controls passed,
the separate seeded reference audit agreed on 500 valid vectors and rejected
500 corruptions, and `py_compile` passed. These are construction/preparation
checks, not the post-freeze allocation result; the frozen runner retains a
fresh 12-test execution plus the independent audit output.
