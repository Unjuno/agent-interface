# #59/#5156 per-admission to owner-key-up context join A01

## H / T / D / C / U

**H.** The A02 owner-thread KeyRelease/XSync receipt can pass through current-main `doom_retained_input_backend_v4` and remain joined to that backend's existing `id`, `step`, and admission position for reverse-order multi-key releases and repeated same-key cycles, without changing release order or the backend's existing post-batch outcome.

**T.** One new deterministic WSLc fake-Xlib composition candidate loads the exact current-main retained backend v4 with the A02 InputOwner v11 / transition wrapper v4 candidate. It runs two cases: A+B admitted then released B+A, and two sequential C down/up cycles. The separate raw-only auditor reconstructs admission/release pairs, nested caller/owner timestamps, XTest/XSync order, final neutral keymap, and six corruption controls. This is a distinct successor to A02 and does not rerun A01 or A02.

**D.** `PASS_OWNER_KEYUP_CONTEXT_JOIN_SCOPED` only if both case traces contain exact admission and release cardinality; each release keeps the correct `id`/`step`/admission position and key through reverse-order or repeated cycles; each nested owner receipt matches owner/token/keycode and is inside the caller interval; existing batch verification remains true while physical-authority fields remain false; XTest/XSync order matches the baseline contract; the fake keymap is neutral after verified owner cleanup; source hashes match; and all six mutations are rejected. Otherwise FAIL/STOP.

## Frozen inputs and execution limits

- Current-main intake commit: `ad7a6d5a6dcc0d990af5a2beef32d59b31fbaa04`.
- Baseline blobs: `input_owner_v10.py` `341b3c01649943ddaad5f28431a792c4889cc36e`; `input_transition_owner_v3.py` `99dfc7c9907b018e7473bc2ba8a7393a5b221f51`; current-main retained backend v4 `doom_retained_input_backend_v4.py` `81484e6146bb8b93a007f338df3e504620924a45`.
- A02 candidate/wrapper are copied byte-for-byte; all baseline, candidate, fake-Xlib, runner, auditor, and protocol hashes are in `FREEZE.json`.
- WSLc image is the already inspected local immutable `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (image ID `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`), linux/amd64, Python 3.12.15. No pull, network, GUI, X server, or physical input.
- Candidate once and auditor once only after candidate exit 0, each in its own disposable one-CPU container; source mount read-only, output separate and writable, memory cap omitted, zero retries.

**C.** Fake-Xlib and a stubbed outer executor cannot establish server-side behavior, scheduling, map activity, visual feedback usefulness, recovery, or game effects. Repeated same-key cycles and reverse-order releases are narrow source-composition controls.

**U.** This is a scoped context-join construction result only. It grants no X11/live allocation or input authority and does not meet #59's matched live threat-exposure, useful-feedback, bounded-recovery, or MAP01 outcome gate.
